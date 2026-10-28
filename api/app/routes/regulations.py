"""Admin: regulation documents and rule sets per project type, one set per verification scope."""

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
from app.deps import OcrDep, SessionDep, SessionsDep, SettingsDep
from app.documents.ingest import new_regulation_document, read_upload
from app.documents.ocr_jobs import read_scanned_regulation
from app.models import RegulationDocument, RegulationRule
from app.routes.problems import PROBLEMS
from app.routes.project_types import existing_project_type
from app.verification.checks import list_checks, validated_params
from app.vocabulary import OcrStatus, RuleKind, Scope, Severity

router = APIRouter(
    prefix="/api",
    tags=["regulations"],
    dependencies=[Depends(require_roles(Role.ADMIN))],
    responses=PROBLEMS,
)
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]


class CheckOut(BaseModel):
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
    scanned_pages: int  # pages without a text layer
    ocr_status: OcrStatus | None  # how reading them went; None when there are none


class RuleIn(BaseModel):
    code: str
    title: str
    description: str = ""
    kind: RuleKind
    check_id: str | None = None
    params: dict[str, Any] = {}
    severity: Severity = Severity.BAD
    active: bool = True


class RuleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    check_id: str | None = None
    params: dict[str, Any] | None = None
    severity: Severity | None = None
    active: bool | None = None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    description: str
    kind: RuleKind
    check_id: str | None
    params: dict[str, Any]
    severity: Severity
    active: bool


class RegulationSet(BaseModel):
    project_type_id: int
    scope: Scope
    documents: list[RegulationDocumentOut]
    rules: list[RuleOut]


@router.get("/checks")
async def checks() -> list[CheckOut]:
    """The deterministic checks a rule of kind "check" can name, with their params."""
    return [
        CheckOut(
            id=spec.id,
            description=spec.description,
            params_schema=spec.params_model.model_json_schema(),
        )
        for spec in list_checks()
    ]


@router.get("/project-types/{project_type_id}/regulations/{scope}")
async def regulation_set(project_type_id: int, scope: Scope, session: SessionDep) -> RegulationSet:
    await existing_project_type(session, project_type_id)
    documents = await session.scalars(
        select(RegulationDocument)
        .where(
            RegulationDocument.project_type_id == project_type_id,
            RegulationDocument.verification_scope == scope,
        )
        .order_by(RegulationDocument.id)
    )
    rules = await session.scalars(
        select(RegulationRule)
        .where(
            RegulationRule.project_type_id == project_type_id,
            RegulationRule.verification_scope == scope,
        )
        .order_by(RegulationRule.id)
    )
    return RegulationSet(
        project_type_id=project_type_id,
        scope=scope,
        documents=[RegulationDocumentOut.model_validate(row) for row in documents],
        rules=[RuleOut.model_validate(row) for row in rules],
    )


@router.post(
    "/project-types/{project_type_id}/regulations/{scope}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_regulation(
    project_type_id: int,
    scope: Scope,
    file: UploadFile,
    background: BackgroundTasks,
    session: SessionDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    ocr: OcrDep,
    admin: Admin,
) -> RegulationDocumentOut:
    """Stores the regulation; scanned pages are then read by OCR in the background."""
    await existing_project_type(session, project_type_id)
    content = await file.read()
    pages = await read_upload(content, settings.max_upload_mb)
    document = new_regulation_document(
        project_type_id,
        scope,
        file.filename or "regulation.pdf",
        content,
        pages,
        admin.id,
        ocr_available=ocr is not None,
    )
    session.add(document)
    await session.commit()
    if ocr and document.ocr_status == OcrStatus.PENDING:
        background.add_task(read_scanned_regulation, sessions, ocr, settings, document.id)
    return RegulationDocumentOut.model_validate(document)


@router.post("/regulation-documents/{document_id}/read-scans", status_code=status.HTTP_202_ACCEPTED)
async def read_regulation_scans_again(
    document_id: int,
    background: BackgroundTasks,
    session: SessionDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    ocr: OcrDep,
) -> RegulationDocumentOut:
    """Reads the regulation's scanned pages once more, after a failure or a stalled reading."""
    document = await session.get(RegulationDocument, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regulation document not found.")
    if ocr is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OCR is switched off (OCR_ENGINE=none), so scanned pages cannot be read.",
        )
    if not document.scanned_pages:
        raise HTTPException(status.HTTP_409_CONFLICT, "This regulation has no scanned pages.")
    document.ocr_status = OcrStatus.PENDING
    await session.commit()
    background.add_task(read_scanned_regulation, sessions, ocr, settings, document.id)
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
    document = await session.get(RegulationDocument, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regulation document not found.")
    await session.delete(document)
    await session.commit()


@router.post(
    "/project-types/{project_type_id}/regulations/{scope}/rules",
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    project_type_id: int, scope: Scope, body: RuleIn, session: SessionDep
) -> RuleOut:
    await existing_project_type(session, project_type_id)
    _validate(body.kind, body.check_id, body.params)
    rule = RegulationRule(
        project_type_id=project_type_id, verification_scope=scope, **body.model_dump()
    )
    if body.kind == RuleKind.AI:
        rule.check_id = None
    session.add(rule)
    try:
        await session.commit()
    except IntegrityError as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"The {scope} rule set already has a rule {body.code!r}."
        ) from error
    return RuleOut.model_validate(rule)


@router.patch("/rules/{rule_id}")
async def update_rule(rule_id: int, body: RuleUpdate, session: SessionDep) -> RuleOut:
    rule = await _existing_rule(session, rule_id)
    for name, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, name, value)
    _validate(RuleKind(rule.kind), rule.check_id, rule.params)
    await session.commit()
    return RuleOut.model_validate(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: int, session: SessionDep) -> None:
    await session.delete(await _existing_rule(session, rule_id))
    await session.commit()


def _validate(kind: RuleKind, check_id: str | None, params: dict[str, Any]) -> None:
    """A check rule must name a registered check with valid params (InvalidCheckError -> 422)."""
    if kind == RuleKind.CHECK:
        validated_params(check_id, params)


async def _existing_rule(session: AsyncSession, rule_id: int) -> RegulationRule:
    rule = await session.get(RegulationRule, rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found.")
    return rule
