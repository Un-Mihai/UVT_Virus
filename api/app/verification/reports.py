"""Read side: the latest run of a scope and the findings a role may see from it."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DocumentFinding, VerificationRun
from app.pdf import HighlightMark
from app.verification.scope import Visibility
from app.vocabulary import Severity

HIGHLIGHT_COLORS = {Severity.BAD: "f28b82", Severity.WARN: "fdd663"}


def anchor(finding: DocumentFinding) -> str:
    """The id the document viewer scrolls to (DESIGN.md: #finding-{id})."""
    return f"finding-{finding.id}"


async def latest_run(
    session: AsyncSession, project_id: int, visibility: Visibility
) -> VerificationRun | None:
    return await session.scalar(
        select(VerificationRun)
        .where(VerificationRun.project_id == project_id, VerificationRun.scope == visibility.scope)
        .order_by(VerificationRun.id.desc())
        .limit(1)
    )


async def visible_findings(
    session: AsyncSession,
    run: VerificationRun,
    visibility: Visibility,
    document_id: int | None = None,
) -> Sequence[DocumentFinding]:
    """The run's findings in the viewer's scope at or above their confidence threshold."""
    query = select(DocumentFinding).where(
        DocumentFinding.run_id == run.id,
        DocumentFinding.scope == visibility.scope,
        DocumentFinding.confidence >= visibility.min_confidence,
    )
    if document_id is not None:
        query = query.where(DocumentFinding.document_id == document_id)
    order = (DocumentFinding.document_id, DocumentFinding.page, DocumentFinding.id)
    return (await session.scalars(query.order_by(*order))).all()


def is_visible(finding: DocumentFinding, visibility: Visibility) -> bool:
    return finding.scope == visibility.scope and finding.confidence >= visibility.min_confidence


def highlight_marks(findings: Sequence[DocumentFinding], locale: str) -> list[HighlightMark]:
    """One annotation per finding with boxes, its note in `locale` (English as fallback)."""

    def text(localized: dict[str, str]) -> str:
        return localized.get(locale) or localized.get("en") or ""

    return [
        HighlightMark(
            page=finding.page,
            rects=[(x0, top, x1, bottom) for x0, top, x1, bottom in finding.rects],
            anchor=anchor(finding),
            note=f"{text(finding.reason)}\n{text(finding.recommendation)}",
            color=HIGHLIGHT_COLORS[Severity(finding.severity)],
        )
        for finding in findings
        if finding.page is not None and finding.rects
    ]
