"""Where the reading of scanned pages stands, for the API answers and the verification gate."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DocumentPage, ProjectDocument
from app.vocabulary import OcrStatus

# shortcut: OCR runs in the API process (BackgroundTasks), so a restart or scale-to-zero loses
# the job; pages no one finished reading for this long count as stalled and can be read again.
# Move to a job queue if documents get long.
STALL_AFTER = timedelta(minutes=15)


@dataclass(frozen=True)
class Reading:
    scanned: int  # pages without a text layer
    reading: int  # still waiting for OCR
    unreadable: int  # OCR failed or is not configured
    stalled: bool  # waiting, but nothing moved for STALL_AFTER


def reading_of(pages: Sequence[DocumentPage], now: datetime | None = None) -> Reading:
    now = now or datetime.now(UTC)
    pending = [page for page in pages if page.ocr_status == OcrStatus.PENDING]
    last_move = max((page.ocr_updated_at for page in pages if page.ocr_updated_at), default=None)
    return Reading(
        scanned=sum(page.is_scan for page in pages),
        reading=len(pending),
        unreadable=sum(
            page.ocr_status in (OcrStatus.FAILED, OcrStatus.UNAVAILABLE) for page in pages
        ),
        stalled=bool(pending) and (last_move is None or now - last_move > STALL_AFTER),
    )


async def project_still_reading(session: AsyncSession, project_id: int) -> bool:
    """True while some document of the project has scanned pages OCR is still reading."""
    rows = await session.scalars(
        select(DocumentPage)
        .join(ProjectDocument, ProjectDocument.id == DocumentPage.document_id)
        .where(ProjectDocument.project_id == project_id, DocumentPage.is_scan)
    )
    by_document: dict[int, list[DocumentPage]] = {}
    for page in rows:
        by_document.setdefault(page.document_id, []).append(page)
    return any(
        (state := reading_of(pages)).reading and not state.stalled for pages in by_document.values()
    )
