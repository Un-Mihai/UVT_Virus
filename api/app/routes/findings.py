"""People decide: confirm or dismiss a finding. The product never decides on its own."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import CurrentUser, Role, require_roles
from app.deps import SessionDep, VisibilityDep
from app.models import DocumentFinding, ProjectDocument, VerificationRun
from app.projects.access import visible_project
from app.routes.problems import PROBLEMS
from app.routes.verifications import FindingOut, finding_out
from app.verification.reports import is_visible
from app.vocabulary import Decision

router = APIRouter(
    prefix="/api/findings",
    tags=["verification"],
    dependencies=[Depends(require_roles(Role.CLIENT, Role.REVIEWER))],
    responses=PROBLEMS,
)


class DecisionIn(BaseModel):
    decision: Decision | None  # None clears an earlier decision
    note: str | None = None


@router.post("/{finding_id}/decision")
async def decide(
    finding_id: int,
    body: DecisionIn,
    session: SessionDep,
    user: CurrentUser,
    visibility: VisibilityDep,
) -> FindingOut:
    """Only on findings the caller can see: their scope, at or above their threshold."""
    finding = await session.get(DocumentFinding, finding_id)
    if finding is None or not is_visible(finding, visibility):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")
    run = await session.get_one(VerificationRun, finding.run_id)
    await visible_project(session, user, run.project_id)
    finding.decision = body.decision
    finding.decision_note = body.note if body.decision else None
    finding.decided_by = user.id if body.decision else None
    finding.decided_at = datetime.now(UTC) if body.decision else None
    await session.commit()
    document = (
        await session.get(ProjectDocument, finding.document_id) if finding.document_id else None
    )
    return finding_out(finding, document.filename if document else None)
