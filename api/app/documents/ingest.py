"""Stores uploaded PDFs once: raw bytes, text and word boxes per page, personal identifiers.

Pages without a text layer are stored empty and marked for OCR; app/documents/ocr_jobs.py
reads them in the background.
"""

import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models import (
    DocumentPage,
    PersonalIdentifier,
    Project,
    ProjectDocument,
    RegulationDocument,
)
from app.pdf import PageContent, PdfReadError, read_pdf
from app.personal_data import IdentifierHasher, detect_all
from app.vocabulary import IndexStatus, OcrStatus, Scope


class UploadRejectedError(ValueError):
    status_code = 400


class FileTooLargeError(UploadRejectedError):
    status_code = 413


class UnsupportedFileError(UploadRejectedError):
    status_code = 415


async def read_upload(content: bytes, max_upload_mb: int) -> list[PageContent]:
    """Pages of an uploaded PDF, after the checks every upload must pass."""
    if len(content) > max_upload_mb * 1024 * 1024:
        raise FileTooLargeError(f"The file is larger than {max_upload_mb} MB.")
    if not content.startswith(b"%PDF-"):
        raise UnsupportedFileError("Only PDF files can be uploaded.")
    try:
        # pdfplumber is synchronous and CPU-bound; keep it off the event loop.
        return await run_in_threadpool(read_pdf, content)
    except PdfReadError as error:
        raise UnsupportedFileError(str(error)) from error


def initial_ocr_status(page: PageContent, ocr_available: bool) -> OcrStatus | None:
    if not page.is_scan:
        return None
    return OcrStatus.PENDING if ocr_available else OcrStatus.UNAVAILABLE


async def add_project_document(
    session: AsyncSession,
    project: Project,
    filename: str,
    content: bytes,
    pages: list[PageContent],
    hasher: IdentifierHasher,
    ocr_available: bool,
) -> ProjectDocument:
    now = datetime.now(UTC)
    document = ProjectDocument(
        project_id=project.id,
        filename=filename,
        sha256=hashlib.sha256(content).hexdigest(),
        content=content,
        page_count=len(pages),
        pages=[
            DocumentPage(
                number=page.number,
                text=page.text,
                width=page.width,
                height=page.height,
                words=[[w.text, w.x0, w.top, w.x1, w.bottom] for w in page.words],
                is_scan=page.is_scan,
                ocr_status=initial_ocr_status(page, ocr_available),
                ocr_updated_at=now if page.is_scan else None,
            )
            for page in pages
        ],
    )
    session.add(document)
    await session.flush()
    for page in pages:
        await record_identifiers(session, project.id, document.id, page.number, page.text, hasher)
    return document


async def record_identifiers(
    session: AsyncSession,
    project_id: int,
    document_id: int,
    page_number: int,
    text: str,
    hasher: IdentifierHasher,
) -> None:
    """Replaces a page's personal identifiers with those found in `text` (hashed, masked)."""
    await session.execute(
        delete(PersonalIdentifier).where(
            PersonalIdentifier.document_id == document_id,
            PersonalIdentifier.page == page_number,
        )
    )
    for detection in detect_all(text):
        session.add(
            PersonalIdentifier(
                project_id=project_id,
                document_id=document_id,
                page=page_number,
                kind=detection.kind,
                value_hash=hasher.hash(detection.kind, detection.value),
                masked=hasher.mask(detection.value),
                valid=detection.valid,
                start=detection.start,
                end=detection.end,
            )
        )


def regulation_text(pages: Iterable[tuple[int, str]]) -> str:
    """A regulation's text as one string, each page under a "[Page n]" line."""
    return "\n\n".join(f"[Page {number}]\n{text}" for number, text in pages if text)


def new_regulation_document(
    scope: Scope,
    filename: str,
    content: bytes,
    pages: list[PageContent],
    uploaded_by: str,
    *,
    project_type_id: int | None,
    project_id: int | None,
    ocr_available: bool,
) -> RegulationDocument:
    """A regulation for every project (no type, no project), a project type, or one project;
    app/regulations/processing.py then reads its scans and indexes its passages."""
    scanned = sum(page.is_scan for page in pages)
    status = None
    if scanned:
        status = OcrStatus.PENDING if ocr_available else OcrStatus.UNAVAILABLE
    return RegulationDocument(
        project_type_id=project_type_id,
        project_id=project_id,
        verification_scope=scope,
        filename=filename,
        sha256=hashlib.sha256(content).hexdigest(),
        content=content,
        text=regulation_text((page.number, page.text) for page in pages),
        uploaded_by=uploaded_by,
        scanned_pages=scanned,
        ocr_status=status,
        index_status=IndexStatus.PENDING,
    )
