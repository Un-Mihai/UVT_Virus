"""Start a verification run in the caller's scope, then read its findings and highlights."""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, Role, require_roles
from app.deps import HasherDep, OrchestratorDep, SessionDep, SessionsDep, VisibilityDep
from app.documents.reading import project_still_reading
from app.models import DocumentFinding, DocumentPage, ProjectDocument, VerificationRun
from app.pdf import annotate_pdf
from app.projects.access import visible_project
from app.routes.problems import PROBLEMS
from app.routes.projects import project_document
from app.verification.reports import (
    anchor,
    highlight_marks,
    latest_run,
    visible_findings,
)
from app.verification.runner import is_stale, run_verification
from app.vocabulary import Decision, RunStatus, Scope, Severity

router = APIRouter(
    prefix="/api/projects/{project_id}",
    tags=["verification"],
    dependencies=[Depends(require_roles(Role.CLIENT, Role.REVIEWER))],
    responses=PROBLEMS,
)


class RunOut(BaseModel):
    id: int
    scope: Scope
    status: RunStatus
    error: str | None
    created_at: datetime
    finished_at: datetime | None


class FindingOut(BaseModel):
    id: int
    anchor: str  # "finding-{id}": the highlight's id in the viewer and the annotated PDF
    rule_code: str
    agent: str
    severity: Severity
    confidence: float
    reason: dict[str, str]  # {"en": ..., "ro": ...}; show the reader's language
    recommendation: dict[str, str]
    # The evidence was read by OCR, and `confidence` is capped at how sure the reading was.
    ocr: bool
    document_id: int | None
    document_name: str | None
    page: int | None
    quote: str | None
    rects: list[list[float]]  # [x0, top, x1, bottom] in PDF points from the page's top-left
    decision: Decision | None
    decision_note: str | None
    decided_by: str | None
    decided_at: datetime | None


class VerificationReport(BaseModel):
    run: RunOut
    min_confidence: float
    findings: list[FindingOut]


class PageSize(BaseModel):
    number: int
    width: float
    height: float
    is_scan: bool


class DocumentHighlights(BaseModel):
    document_id: int
    filename: str
    run_id: int | None
    pages: list[PageSize]
    findings: list[FindingOut]


@router.post("/verifications", status_code=status.HTTP_202_ACCEPTED)
async def start_verification(
    project_id: int,
    background: BackgroundTasks,
    session: SessionDep,
    sessions: SessionsDep,
    orchestrator: OrchestratorDep,
    hasher: HasherDep,
    user: CurrentUser,
    visibility: VisibilityDep,
) -> RunOut:
    """Starts the Client or Reviewer Verification Process, chosen by the caller's role."""
    await visible_project(session, user, project_id)
    previous = await latest_run(session, project_id, visibility)
    if (
        previous
        and previous.status in (RunStatus.PENDING, RunStatus.RUNNING)
        and not is_stale(previous)
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A verification of this project is already running."
        )
    if await project_still_reading(session, project_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Scanned pages are still being read. Start the check when they are done.",
        )
    run = VerificationRun(project_id=project_id, scope=visibility.scope, started_by=user.id)
    session.add(run)
    await session.commit()
    background.add_task(run_verification, sessions, orchestrator, hasher, run.id)
    return _run_out(run)


@router.get("/verifications/latest")
async def latest_verification(
    project_id: int, session: SessionDep, user: CurrentUser, visibility: VisibilityDep
) -> VerificationReport:
    """The latest run in the caller's scope, with only the findings their role may see."""
    await visible_project(session, user, project_id)
    run = await latest_run(session, project_id, visibility)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This project has not been verified yet.")
    findings = await visible_findings(session, run, visibility)
    return VerificationReport(
        run=_run_out(run),
        min_confidence=float(visibility.min_confidence),
        findings=await findings_out(session, findings),
    )


@router.get("/documents/{document_id}/highlights")
async def document_highlights(
    project_id: int,
    document_id: int,
    session: SessionDep,
    user: CurrentUser,
    visibility: VisibilityDep,
) -> DocumentHighlights:
    """Page sizes and highlight boxes, for drawing overlays on the rendered original PDF."""
    await visible_project(session, user, project_id)
    document = await project_document(session, project_id, document_id)
    pages = await session.scalars(
        select(DocumentPage)
        .where(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.number)
    )
    run = await latest_run(session, project_id, visibility)
    findings = await visible_findings(session, run, visibility, document_id) if run else []
    return DocumentHighlights(
        document_id=document.id,
        filename=document.filename,
        run_id=run.id if run else None,
        pages=[
            PageSize(number=p.number, width=p.width, height=p.height, is_scan=p.is_scan)
            for p in pages
        ],
        findings=await findings_out(session, findings),
    )


@router.get(
    "/documents/{document_id}/annotated",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def annotated_document(
    project_id: int,
    document_id: int,
    session: SessionDep,
    user: CurrentUser,
    visibility: VisibilityDep,
    lang: Literal["en", "ro"] = "en",
) -> Response:
    """The original PDF with a Highlight annotation per visible finding (/NM = its anchor),
    its notes in `lang`."""
    await visible_project(session, user, project_id)
    document = await project_document(session, project_id, document_id, with_content=True)
    run = await latest_run(session, project_id, visibility)
    findings = await visible_findings(session, run, visibility, document_id) if run else []
    return Response(
        annotate_pdf(document.content, highlight_marks(findings, lang)),
        media_type="application/pdf",
    )


def _run_out(run: VerificationRun) -> RunOut:
    stale = is_stale(run)
    return RunOut(
        id=run.id,
        scope=Scope(run.scope),
        status=RunStatus.FAILED if stale else RunStatus(run.status),
        error="The run was interrupted; start it again." if stale else run.error,
        created_at=run.created_at,
        finished_at=run.finished_at,
    )


async def findings_out(
    session: AsyncSession, findings: Sequence[DocumentFinding]
) -> list[FindingOut]:
    ids = {finding.document_id for finding in findings if finding.document_id}
    rows = await session.execute(
        select(ProjectDocument.id, ProjectDocument.filename).where(ProjectDocument.id.in_(ids))
    )
    names = dict(rows.all())
    return [finding_out(finding, names.get(finding.document_id or 0)) for finding in findings]


def finding_out(finding: DocumentFinding, document_name: str | None) -> FindingOut:
    return FindingOut(
        id=finding.id,
        anchor=anchor(finding),
        rule_code=finding.rule_code,
        agent=finding.agent,
        severity=Severity(finding.severity),
        confidence=float(finding.confidence),
        reason=finding.reason,
        recommendation=finding.recommendation,
        ocr=finding.ocr,
        document_id=finding.document_id,
        document_name=document_name,
        page=finding.page,
        quote=finding.quote,
        rects=finding.rects,
        decision=Decision(finding.decision) if finding.decision else None,
        decision_note=finding.decision_note,
        decided_by=finding.decided_by,
        decided_at=finding.decided_at,
    )
