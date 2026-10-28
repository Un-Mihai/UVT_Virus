"""Admin: regulation PDFs and written rules, each for the client or the reviewer scope.

Levels: a regulation PDF applies to every project (no type, no project), to every project of a
type, or to one project. Written rules apply to every project or to a type. A check uses all
the levels that reach the project (app/regulations/levels.py).
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.auth import Role, User, require_roles
from app.deps import AIDep, OcrDep, SessionDep, SessionsDep, SettingsDep
from app.documents.ingest import new_regulation_document, read_upload
from app.models import Project, RegulationDocument, RegulationRule
from app.regulations.processing import process_regulation
from app.routes.problems import PROBLEMS
from app.routes.project_types import existing_project_type
from app.verification.checks import list_checks
from app.vocabulary import IndexStatus, OcrStatus, ProjectStatus, Scope, Severity

router = APIRouter(
    prefix="/api",
    tags=["regulations"],
    dependencies=[Depends(require_roles(Role.ADMIN))],
    responses=PROBLEMS,
)
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]


class CheckOut(BaseModel):
    """A code check the model may ask for while it compares documents with regulations."""

    id: str
    description: dict[str, str]  # {"en": ..., "ro": ...}
    params_schema: dict[str, Any]


class RegulationDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    sha256: str
    uploaded_by: str
    created_at: datetime
    project_type_id: int | None  # with project_id: both None means every project
    project_id: int | None
    scanned_pages: int  # pages without a text layer
    ocr_status: OcrStatus | None  # how reading them went; None when there are none
    # Whether the passages are embedded and searchable; checks fall back to reading the
    # regulation from its start when they are not.
    index_status: IndexStatus
    index_error: str | None


class RuleIn(BaseModel):
    """A requirement in plain words; the model judges documents against it."""

    scope: Scope
    project_type_id: int | None = None  # None: every project
    code: str
    title: str
    description: str
    severity: Severity = Severity.BAD


class RuleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: Severity | None = None
    active: bool | None = None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_type_id: int | None
    code: str
    title: str
    description: str
    severity: Severity
    active: bool


class RegulationSet(BaseModel):
    """What one level holds for one scope (not what it inherits from wider levels)."""

    scope: Scope
    project_type_id: int | None
    project_id: int | None
    documents: list[RegulationDocumentOut]
    rules: list[RuleOut]  # always empty for a single project: projects get regulation PDFs


class AdminProjectOut(BaseModel):
    """A project an admin can attach regulations to."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    project_type_id: int
    status: ProjectStatus


async def _check_level(
    session: AsyncSession, project_type_id: int | None, project_id: int | None
) -> None:
    if project_type_id is not None and project_id is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Choose a project type or a project, not both."
        )
    if project_type_id is not None:
        await existing_project_type(session, project_type_id)
    if project_id is not None and await session.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")


@router.get("/checks")
async def checks() -> list[CheckOut]:
    """The code checks the model may ask for while comparing documents with regulations."""
    return [
        CheckOut(
            id=spec.id,
            description=spec.description,
            params_schema=spec.params_model.model_json_schema(),
        )
        for spec in list_checks()
    ]


@router.get("/admin/projects")
async def admin_projects(session: SessionDep) -> list[AdminProjectOut]:
    """Every project, newest first, so an admin can attach regulations to one."""
    rows = await session.scalars(select(Project).order_by(Project.id.desc()))
    return [AdminProjectOut.model_validate(row) for row in rows]


@router.get("/regulations")
async def regulation_set(
    session: SessionDep,
    scope: Scope,
    project_type_id: int | None = None,
    project_id: int | None = None,
) -> RegulationSet:
    """The regulation PDFs and written rules of one level; no type and no project means every
    project."""
    await _check_level(session, project_type_id, project_id)
    documents = await session.scalars(
        select(RegulationDocument)
        .where(
            RegulationDocument.verification_scope == scope,
            RegulationDocument.project_type_id.is_not_distinct_from(project_type_id),
            RegulationDocument.project_id.is_not_distinct_from(project_id),
        )
        .order_by(RegulationDocument.id)
    )
    rules: list[RuleOut] = []
    if project_id is None:
        rows = await session.scalars(
            select(RegulationRule)
            .where(
                RegulationRule.verification_scope == scope,
                RegulationRule.project_type_id.is_not_distinct_from(project_type_id),
            )
            .order_by(RegulationRule.id)
        )
        rules = [RuleOut.model_validate(row) for row in rows]
    return RegulationSet(
        scope=scope,
        project_type_id=project_type_id,
        project_id=project_id,
        documents=[RegulationDocumentOut.model_validate(row) for row in documents],
        rules=rules,
    )


@router.post("/regulations/documents", status_code=status.HTTP_201_CREATED)
async def upload_regulation(
    file: UploadFile,
    background: BackgroundTasks,
    session: SessionDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    ai: AIDep,
    ocr: OcrDep,
    admin: Admin,
    scope: Scope,
    project_type_id: int | None = None,
    project_id: int | None = None,
) -> RegulationDocumentOut:
    """Stores a regulation PDF; it is then read (OCR for scans), split into passages and
    embedded in the background, so checks can retrieve what applies to each document."""
    await _check_level(session, project_type_id, project_id)
    content = await file.read()
    pages = await read_upload(content, settings.max_upload_mb)
    document = new_regulation_document(
        scope,
        file.filename or "regulation.pdf",
        content,
        pages,
        admin.id,
        project_type_id=project_type_id,
        project_id=project_id,
        ocr_available=ocr is not None,
    )
    session.add(document)
    await session.commit()
    background.add_task(process_regulation, sessions, ai, ocr, settings, document.id)
    return RegulationDocumentOut.model_validate(document)


@router.post("/regulation-documents/{document_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_regulation_again(
    document_id: int,
    background: BackgroundTasks,
    session: SessionDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    ai: AIDep,
    ocr: OcrDep,
) -> RegulationDocumentOut:
    """Reads, splits and embeds the regulation once more: after a failure, a stalled job, or
    a change of embedding model or AI provider."""
    document = await _existing_regulation(session, document_id)
    document.index_status, document.index_error = IndexStatus.PENDING, None
    if document.scanned_pages and ocr is not None:
        document.ocr_status = OcrStatus.PENDING
    await session.commit()
    background.add_task(process_regulation, sessions, ai, ocr, settings, document.id)
    return RegulationDocumentOut.model_validate(document)


@router.get(
    "/regulation-documents/{document_id}/file",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def regulation_file(document_id: int, session: SessionDep) -> Response:
    document = await session.get(
        RegulationDocument, document_id, options=[undefer(RegulationDocument.content)]
    )
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regulation document not found.")
    return Response(document.content, media_type="application/pdf")


@router.delete("/regulation-documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_regulation(document_id: int, session: SessionDep) -> None:
    await session.delete(await _existing_regulation(session, document_id))
    await session.commit()


@router.post("/regulations/rules", status_code=status.HTTP_201_CREATED)
async def create_rule(body: RuleIn, session: SessionDep) -> RuleOut:
    if body.project_type_id is not None:
        await existing_project_type(session, body.project_type_id)
    rule = RegulationRule(
        project_type_id=body.project_type_id,
        verification_scope=body.scope,
        code=body.code,
        title=body.title,
        description=body.description,
        severity=body.severity,
    )
    session.add(rule)
    try:
        await session.commit()
    except IntegrityError as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"This rule set already has a rule {body.code!r}."
        ) from error
    return RuleOut.model_validate(rule)


@router.patch("/rules/{rule_id}")
async def update_rule(rule_id: int, body: RuleUpdate, session: SessionDep) -> RuleOut:
    rule = await _existing_rule(session, rule_id)
    for name, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, name, value)
    await session.commit()
    return RuleOut.model_validate(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: int, session: SessionDep) -> None:
    await session.delete(await _existing_rule(session, rule_id))
    await session.commit()


async def _existing_regulation(session: AsyncSession, document_id: int) -> RegulationDocument:
    document = await session.get(RegulationDocument, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regulation document not found.")
    return document


async def _existing_rule(session: AsyncSession, rule_id: int) -> RegulationRule:
    rule = await session.get(RegulationRule, rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found.")
    return rule
