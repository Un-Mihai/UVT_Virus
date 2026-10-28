"""A project's list of documents to add. Whoever can open the project reads it (an admin can read
any); only admins change it. Without an admin's edits the list is read from the regulations that
apply to the project (app/projects/required_documents.py)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, Role, User, current_user, require_roles
from app.deps import AIDep, SessionDep, SessionsDep, SettingsDep
from app.models import Project, RegulationDocument, RequiredDocument
from app.projects.access import visible_project
from app.projects.required_documents import read_regulations
from app.routes.problems import PROBLEMS
from app.vocabulary import RequiredDocumentSource

router = APIRouter(
    prefix="/api",
    tags=["required documents"],
    dependencies=[Depends(current_user)],
    responses=PROBLEMS,
)
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RequiredDocumentIn(BaseModel):
    name: Name
    description: Text = ""


class RequiredDocumentUpdate(BaseModel):
    name: Name | None = None
    description: Text | None = None


class RequiredDocumentOut(BaseModel):
    id: int
    name: str
    description: str
    source: RequiredDocumentSource
    # Where a regulations item was read; the regulation's own words, when it was quoted exactly.
    regulation_filename: str | None
    regulation_page: int | None
    regulation_quote: str | None


@router.get("/projects/{project_id}/required-documents")
async def required_documents(
    project_id: int, session: SessionDep, user: CurrentUser
) -> list[RequiredDocumentOut]:
    if user.has_role(Role.ADMIN):
        await _project(session, project_id)
    else:
        await visible_project(session, user, project_id)
    return await _items(session, project_id)


@router.post("/projects/{project_id}/required-documents", status_code=status.HTTP_201_CREATED)
async def add_required_document(
    project_id: int, body: RequiredDocumentIn, session: SessionDep, _: Admin
) -> RequiredDocumentOut:
    await _project(session, project_id)
    item = RequiredDocument(
        project_id=project_id,
        name=body.name,
        description=body.description,
        source=RequiredDocumentSource.ADMIN,
    )
    session.add(item)
    await session.commit()
    return _out(item, None)


@router.post("/projects/{project_id}/required-documents/from-regulations")
async def read_required_documents(
    project_id: int,
    session: SessionDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    ai: AIDep,
    _: Admin,
) -> list[RequiredDocumentOut]:
    """Reads the regulations again: items read from them are replaced, an admin's stay."""
    await _project(session, project_id)
    await read_regulations(sessions, ai, settings, project_id)
    return await _items(session, project_id)


@router.patch("/required-documents/{item_id}")
async def update_required_document(
    item_id: int, body: RequiredDocumentUpdate, session: SessionDep, _: Admin
) -> RequiredDocumentOut:
    """An edited item becomes the admin's, so reading the regulations again keeps it."""
    item = await _existing(session, item_id)
    for name, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(item, name, value)
    item.source = RequiredDocumentSource.ADMIN
    await session.commit()
    return next(out for out in await _items(session, item.project_id) if out.id == item.id)


@router.delete("/required-documents/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_required_document(item_id: int, session: SessionDep, _: Admin) -> None:
    await session.delete(await _existing(session, item_id))
    await session.commit()


async def _project(session: AsyncSession, project_id: int) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    return project


async def _existing(session: AsyncSession, item_id: int) -> RequiredDocument:
    item = await session.get(RequiredDocument, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Required document not found.")
    return item


async def _items(session: AsyncSession, project_id: int) -> list[RequiredDocumentOut]:
    rows = await session.execute(
        select(RequiredDocument, RegulationDocument.filename)
        .outerjoin(
            RegulationDocument, RegulationDocument.id == RequiredDocument.regulation_document_id
        )
        .where(RequiredDocument.project_id == project_id)
        .order_by(RequiredDocument.id)
    )
    return [_out(item, filename) for item, filename in rows.all()]


def _out(item: RequiredDocument, filename: str | None) -> RequiredDocumentOut:
    return RequiredDocumentOut(
        id=item.id,
        name=item.name,
        description=item.description,
        source=RequiredDocumentSource(item.source),
        regulation_filename=filename,
        regulation_page=item.regulation_page,
        regulation_quote=item.regulation_quote,
    )
