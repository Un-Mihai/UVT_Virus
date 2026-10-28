"""Reads scanned pages in the background, after the upload has answered.

Each page is saved as soon as it is read, so the web can show progress. Background entry
points never raise: a failure is recorded on the pages instead.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import undefer

from app.config import Settings
from app.documents.ingest import record_identifiers
from app.models import DocumentPage, ProjectDocument
from app.ocr import OcrEngine, OcrFailure, OcrText, read_pages
from app.personal_data import IdentifierHasher
from app.vocabulary import OcrStatus

logger = logging.getLogger(__name__)


async def read_scanned_pages(
    sessions: async_sessionmaker[AsyncSession],
    engine: OcrEngine,
    settings: Settings,
    hasher: IdentifierHasher,
    document_id: int,
) -> None:
    """OCR for every page of the document still waiting for it."""
    async with sessions() as session:
        document = await session.get_one(
            ProjectDocument, document_id, options=[undefer(ProjectDocument.content)]
        )
        content, project_id = document.content, document.project_id
        numbers = list(
            await session.scalars(
                select(DocumentPage.number).where(
                    DocumentPage.document_id == document_id,
                    DocumentPage.ocr_status == OcrStatus.PENDING,
                )
            )
        )
    try:
        async for number, outcome in read_pages(
            content, sorted(numbers), engine, settings.ocr_dpi, settings.ocr_concurrency
        ):
            async with sessions() as session:
                await _save_page(session, document_id, project_id, number, outcome, hasher)
                await session.commit()
    except Exception as error:
        logger.exception("Reading the scans of document %s failed", document_id)
        async with sessions() as session:
            await session.execute(
                update(DocumentPage)
                .where(
                    DocumentPage.document_id == document_id,
                    DocumentPage.ocr_status == OcrStatus.PENDING,
                )
                .values(
                    ocr_status=OcrStatus.FAILED,
                    ocr_error=f"{type(error).__name__}: {error}",
                    ocr_updated_at=datetime.now(UTC),
                )
            )
            await session.commit()


async def _save_page(
    session: AsyncSession,
    document_id: int,
    project_id: int,
    number: int,
    outcome: OcrText | OcrFailure,
    hasher: IdentifierHasher,
) -> None:
    page = await session.scalar(
        select(DocumentPage).where(
            DocumentPage.document_id == document_id, DocumentPage.number == number
        )
    )
    if page is None:  # the document was deleted while it was being read
        return
    page.ocr_updated_at = datetime.now(UTC)
    # The page's text changes, so facts extracted from the old text no longer hold.
    page.facts = None
    page.facts_version = None
    if isinstance(outcome, OcrFailure):
        page.ocr_status, page.ocr_error = OcrStatus.FAILED, outcome.error
        return
    page.text = outcome.text
    page.words = [
        [word.text, word.x0, word.top, word.x1, word.bottom, word.confidence]
        for word in outcome.words
    ]
    page.ocr_status = OcrStatus.DONE if outcome.text.strip() else OcrStatus.FAILED
    page.ocr_error = None if outcome.text.strip() else "No text was found on the page."
    page.ocr_confidence = Decimal(str(outcome.confidence))
    await record_identifiers(session, project_id, document_id, number, outcome.text, hasher)
