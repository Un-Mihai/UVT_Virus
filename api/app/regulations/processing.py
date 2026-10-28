"""Makes an uploaded regulation searchable, in the background: OCR for scanned pages, then
passages, then one embedding per passage. Never raises; outcomes are recorded on the document."""

import logging

import openai
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import undefer
from starlette.concurrency import run_in_threadpool

from app.ai.client import AIClient, AINotConfiguredError, AIResponseError, BudgetExceededError
from app.config import Settings
from app.documents.ingest import regulation_text
from app.models import RegulationDocument, RegulationPassage
from app.ocr import OcrEngine, OcrFailure, read_pages
from app.pdf import PageContent, read_pdf
from app.personal_data import IdentifierHasher, mask_for_model
from app.regulations.chunking import split_pages
from app.vocabulary import IndexStatus, OcrStatus

logger = logging.getLogger(__name__)

EMBED_BATCH = 64
EMBEDDING_ERRORS = (AINotConfiguredError, BudgetExceededError, AIResponseError, openai.APIError)


async def process_regulation(
    sessions: async_sessionmaker[AsyncSession],
    ai: AIClient,
    ocr: OcrEngine | None,
    settings: Settings,
    regulation_id: int,
) -> None:
    try:
        async with sessions() as session:
            regulation = await session.get_one(
                RegulationDocument, regulation_id, options=[undefer(RegulationDocument.content)]
            )
            content = regulation.content
        pages = await run_in_threadpool(read_pdf, content)
        texts = {page.number: page.text for page in pages if page.text}
        ocr_status = await _read_scans(content, pages, ocr, settings, texts)
        hasher = IdentifierHasher(settings.personal_data_hash_key)
        passages = split_pages(
            (page, mask_for_model(text, hasher).text) for page, text in sorted(texts.items())
        )
        vectors, index_status, index_error = await _embed(ai, [text for _, text in passages])
        async with sessions() as session:
            await session.execute(
                delete(RegulationPassage).where(
                    RegulationPassage.regulation_document_id == regulation_id
                )
            )
            session.add_all(
                RegulationPassage(
                    regulation_document_id=regulation_id,
                    page=page,
                    text=text,
                    embedding=vectors[index] if vectors else None,
                    embedding_model=settings.ai_embedding_model if vectors else None,
                )
                for index, (page, text) in enumerate(passages)
            )
            await session.execute(
                update(RegulationDocument)
                .where(RegulationDocument.id == regulation_id)
                .values(
                    text=regulation_text(sorted(texts.items())),
                    ocr_status=ocr_status,
                    index_status=index_status,
                    index_error=index_error,
                )
            )
            await session.commit()
    except Exception as error:
        logger.exception("Processing regulation %s failed", regulation_id)
        async with sessions() as session:
            await session.execute(
                update(RegulationDocument)
                .where(RegulationDocument.id == regulation_id)
                .values(
                    index_status=IndexStatus.FAILED,
                    index_error=f"{type(error).__name__}: {error}",
                )
            )
            await session.commit()


async def _read_scans(
    content: bytes,
    pages: list[PageContent],
    ocr: OcrEngine | None,
    settings: Settings,
    texts: dict[int, str],
) -> OcrStatus | None:
    """OCR for pages without a text layer; their text goes into `texts`."""
    scanned = [page.number for page in pages if page.is_scan]
    if not scanned:
        return None
    if ocr is None:
        return OcrStatus.UNAVAILABLE
    failed = 0
    async for number, outcome in read_pages(
        content, scanned, ocr, settings.ocr_dpi, settings.ocr_concurrency
    ):
        if isinstance(outcome, OcrFailure) or not outcome.text.strip():
            failed += 1
        else:
            texts[number] = outcome.text
    return OcrStatus.FAILED if failed else OcrStatus.DONE


async def _embed(
    ai: AIClient, texts: list[str]
) -> tuple[list[list[float]] | None, IndexStatus, str | None]:
    """Embeddings for every passage, or None with the reason (search then falls back)."""
    if not texts:
        return [], IndexStatus.DONE, None
    vectors: list[list[float]] = []
    try:
        for start in range(0, len(texts), EMBED_BATCH):
            vectors += await ai.embed(
                purpose="index regulation", texts=texts[start : start + EMBED_BATCH]
            )
    except EMBEDDING_ERRORS as error:
        return None, IndexStatus.FAILED, str(error)
    return vectors, IndexStatus.DONE, None
