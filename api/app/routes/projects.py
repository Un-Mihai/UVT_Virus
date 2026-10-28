"""Client applications: form, documents, submission. Reviewers read submitted ones."""

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, undefer

from app.auth import CurrentUser, Role, User, require_roles
from app.deps import HasherDep, OcrDep, SessionDep, SessionsDep, SettingsDep
from app.documents.ingest import add_project_document, read_upload
from app.documents.ocr_jobs import read_scanned_pages
from app.documents.reading import reading_of
from app.models import DocumentPage, PersonalIdentifier, Project, ProjectDocument
from app.personal_data import IdentifierHasher
from app.projects.access import editable_project, visible_project
from app.projects.form import ApplicationForm, stored_form
from app.routes.problems import PROBLEMS
from app.routes.project_types import existing_project_type
from app.verification.reports import reviewed_project_ids
from app.vocabulary import OcrStatus, ProjectStatus, Verdict

router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
    dependencies=[Depends(require_roles(Role.CLIENT, Role.REVIEWER))],
    responses=PROBLEMS,
)
Client = Annotated[User, Depends(require_roles(Role.CLIENT))]
Reviewer = Annotated[User, Depends(require_roles(Role.REVIEWER))]


class ProjectIn(BaseModel):
    project_type_id: int
    title: str
    form: ApplicationForm


class ProjectUpdate(BaseModel):
    title: str | None = None
    form: ApplicationForm | None = None


class VerdictIn(BaseModel):
    verdict: Verdict
    note: str | None = None  # required when asking for changes: what the owner must fix


class PageOut(BaseModel):
    number: int
    width: float  # PDF points; highlight boxes are measured in the same units
    height: float
    # Where the page's text comes from: its text layer, OCR, or nowhere (yet).
    source: Literal["text", "ocr", "none"]
    ocr_status: OcrStatus | None
    ocr_confidence: float | None


class DocumentOut(BaseModel):
    id: int
    filename: str
    sha256: str
    page_count: int
    document_type: str | None
    uploaded_at: datetime
    pages: list[PageOut]
    # Scanned pages still waiting for OCR, but nothing moved for a while: offer to read again.
    reading_stalled: bool


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_type_id: int
    owner_id: str
    owner_name: str | None  # the account that applied
    applicant_name: str | None = None  # the organisation, from the form
    title: str
    status: ProjectStatus
    created_at: datetime
    submitted_at: datetime | None
    # A reviewer has started checking this submitted project.
    in_review: bool = False
    verdict: Verdict | None
    verdict_note: str | None
    verdict_at: datetime | None


class ProjectOut(ProjectSummary):
    form: dict[str, Any]  # the CNP appears only as legal_representative_cnp_masked
    documents: list[DocumentOut]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectIn, session: SessionDep, hasher: HasherDep, client: Client
) -> ProjectOut:
    await existing_project_type(session, body.project_type_id)
    project = Project(
        project_type_id=body.project_type_id,
        owner_id=client.id,
        owner_name=client.display_name,
        title=body.title,
    )
    session.add(project)
    await session.flush()
    await _save_form(session, project, body.form, hasher)
    await session.commit()
    return await _project_out(session, project.id)


@router.get("")
async def list_projects(session: SessionDep, user: CurrentUser) -> list[ProjectSummary]:
    """Clients get their own projects; reviewers get every submitted project."""
    query = select(Project).order_by(Project.id.desc())
    if user.has_role(Role.REVIEWER):
        query = query.where(Project.status == ProjectStatus.SUBMITTED)
    else:
        query = query.where(Project.owner_id == user.id)
    projects = (await session.scalars(query)).all()
    reviewed = await reviewed_project_ids(session, [project.id for project in projects])
    return [project_summary(project, project.id in reviewed) for project in projects]


@router.get("/{project_id}")
async def get_project(project_id: int, session: SessionDep, user: CurrentUser) -> ProjectOut:
    await visible_project(session, user, project_id)
    return await _project_out(session, project_id)


@router.patch("/{project_id}")
async def update_project(
    project_id: int, body: ProjectUpdate, session: SessionDep, hasher: HasherDep, client: Client
) -> ProjectOut:
    project = await editable_project(session, client, project_id)
    project.owner_name = client.display_name
    if body.title is not None:
        project.title = body.title
    if body.form is not None:
        # The form never shows the CNP again, so an empty field keeps the one given before.
        keep_cnp = not (body.form.legal_representative_cnp or "").strip()
        await _save_form(session, project, body.form, hasher, keep_cnp=keep_cnp)
    await session.commit()
    return await _project_out(session, project_id)


@router.post("/{project_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int,
    file: UploadFile,
    background: BackgroundTasks,
    session: SessionDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    hasher: HasherDep,
    ocr: OcrDep,
    client: Client,
) -> DocumentOut:
    """Stores the PDF; scanned pages are then read by OCR in the background."""
    project = await editable_project(session, client, project_id)
    content = await file.read()
    pages = await read_upload(content, settings.max_upload_mb)
    document = await add_project_document(
        session,
        project,
        file.filename or "document.pdf",
        content,
        pages,
        hasher,
        ocr_available=ocr is not None,
    )
    await session.commit()
    if ocr and any(page.is_scan for page in pages):
        background.add_task(read_scanned_pages, sessions, ocr, settings, hasher, document.id)
    return document_out(document)


@router.post(
    "/{project_id}/documents/{document_id}/read-scans",
    status_code=status.HTTP_202_ACCEPTED,
)
async def read_scans_again(
    project_id: int,
    document_id: int,
    background: BackgroundTasks,
    session: SessionDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    hasher: HasherDep,
    ocr: OcrDep,
    user: CurrentUser,
) -> DocumentOut:
    """Reads the scanned pages that failed, or whose reading stalled, once more."""
    await visible_project(session, user, project_id)
    if ocr is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OCR is switched off (OCR_ENGINE=none), so scanned pages cannot be read.",
        )
    document = await project_document(session, project_id, document_id, with_pages=True)
    reading = reading_of(document.pages)
    again = [
        page
        for page in document.pages
        if page.ocr_status in (OcrStatus.FAILED, OcrStatus.UNAVAILABLE)
        or (page.ocr_status == OcrStatus.PENDING and reading.stalled)
    ]
    if not again:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "No scanned page of this document needs reading again."
        )
    now = datetime.now(UTC)
    for page in again:
        page.ocr_status, page.ocr_error, page.ocr_updated_at = OcrStatus.PENDING, None, now
    await session.commit()
    background.add_task(read_scanned_pages, sessions, ocr, settings, hasher, document.id)
    return document_out(document)


@router.delete("/{project_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    project_id: int, document_id: int, session: SessionDep, client: Client
) -> None:
    await editable_project(session, client, project_id)
    document = await project_document(session, project_id, document_id)
    await session.delete(document)
    await session.commit()


@router.get(
    "/{project_id}/documents/{document_id}/file",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def document_file(
    project_id: int, document_id: int, session: SessionDep, user: CurrentUser
) -> Response:
    """The original upload, unchanged, for the document viewer."""
    await visible_project(session, user, project_id)
    document = await project_document(session, project_id, document_id, with_content=True)
    return Response(document.content, media_type="application/pdf")


@router.post("/{project_id}/submit")
async def submit_project(project_id: int, session: SessionDep, client: Client) -> ProjectOut:
    project = await editable_project(session, client, project_id)
    has_documents = await session.scalar(
        select(ProjectDocument.id).where(ProjectDocument.project_id == project_id).limit(1)
    )
    if has_documents is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Upload at least one document before submitting."
        )
    project.status = ProjectStatus.SUBMITTED
    project.submitted_at = datetime.now(UTC)
    project.verdict = project.verdict_note = project.verdict_by = project.verdict_at = None
    await session.commit()
    return await _project_out(session, project_id)


@router.put("/{project_id}/verdict", status_code=status.HTTP_204_NO_CONTENT)
async def record_verdict(
    project_id: int, body: VerdictIn, session: SessionDep, reviewer: Reviewer
) -> None:
    """Approves a submitted project, or sends it back to its owner as a draft to change."""
    project = await visible_project(session, reviewer, project_id)
    note = (body.note or "").strip() or None
    if body.verdict == Verdict.CHANGES_REQUESTED:
        if note is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Say what the applicant must change."
            )
        project.status = ProjectStatus.DRAFT
    project.verdict, project.verdict_note = body.verdict, note
    project.verdict_by, project.verdict_at = reviewer.id, datetime.now(UTC)
    await session.commit()


async def project_document(
    session: AsyncSession,
    project_id: int,
    document_id: int,
    *,
    with_content: bool = False,
    with_pages: bool = False,
) -> ProjectDocument:
    options: list[Any] = [undefer(ProjectDocument.content)] if with_content else []
    if with_pages:
        options.append(selectinload(ProjectDocument.pages))
    document = await session.get(ProjectDocument, document_id, options=options)
    if document is None or document.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")
    return document


def document_out(document: ProjectDocument) -> DocumentOut:
    """The document with its pages; `pages` must be loaded."""
    return DocumentOut(
        id=document.id,
        filename=document.filename,
        sha256=document.sha256,
        page_count=document.page_count,
        document_type=document.document_type,
        uploaded_at=document.uploaded_at,
        pages=[_page_out(page) for page in document.pages],
        reading_stalled=reading_of(document.pages).stalled,
    )


def _page_out(page: DocumentPage) -> PageOut:
    source: Literal["text", "ocr", "none"] = "text"
    if page.is_scan:
        source = "ocr" if page.ocr_status == OcrStatus.DONE else "none"
    return PageOut(
        number=page.number,
        width=page.width,
        height=page.height,
        source=source,
        ocr_status=OcrStatus(page.ocr_status) if page.ocr_status else None,
        ocr_confidence=float(page.ocr_confidence) if page.ocr_confidence is not None else None,
    )


async def _save_form(
    session: AsyncSession,
    project: Project,
    form: ApplicationForm,
    hasher: IdentifierHasher,
    *,
    keep_cnp: bool = False,
) -> None:
    previous = project.form or {}
    project.form, identifiers = stored_form(project.id, form, hasher)
    if keep_cnp:
        if masked := previous.get("legal_representative_cnp_masked"):
            project.form = project.form | {"legal_representative_cnp_masked": masked}
        return
    await session.execute(
        delete(PersonalIdentifier).where(
            PersonalIdentifier.project_id == project.id, PersonalIdentifier.document_id.is_(None)
        )
    )
    session.add_all(identifiers)


def project_summary(project: Project, in_review: bool) -> ProjectSummary:
    return ProjectSummary.model_validate(project).model_copy(
        update={"in_review": in_review, "applicant_name": project.form.get("applicant_name")}
    )


async def _project_out(session: AsyncSession, project_id: int) -> ProjectOut:
    project = await session.get_one(
        Project,
        project_id,
        options=[selectinload(Project.documents).selectinload(ProjectDocument.pages)],
        populate_existing=True,
    )
    reviewed = await reviewed_project_ids(session, [project_id])
    return ProjectOut(
        **project_summary(project, project_id in reviewed).model_dump(),
        form=project.form,
        documents=[document_out(document) for document in project.documents],
    )
