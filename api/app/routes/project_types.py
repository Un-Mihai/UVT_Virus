from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Role, User, current_user, require_roles
from app.deps import SessionDep
from app.models import ProjectType
from app.routes.problems import PROBLEMS

router = APIRouter(
    prefix="/api/project-types",
    tags=["project types"],
    dependencies=[Depends(current_user)],
    responses=PROBLEMS,
)
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]


class ProjectTypeIn(BaseModel):
    code: str
    name: str
    description: str = ""


class ProjectTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class ProjectTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    active: bool


@router.get("")
async def list_project_types(session: SessionDep) -> list[ProjectTypeOut]:
    rows = await session.scalars(select(ProjectType).order_by(ProjectType.name))
    return [ProjectTypeOut.model_validate(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project_type(body: ProjectTypeIn, session: SessionDep, _: Admin) -> ProjectTypeOut:
    project_type = ProjectType(**body.model_dump())
    session.add(project_type)
    try:
        await session.commit()
    except IntegrityError as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"A project type with code {body.code!r} already exists."
        ) from error
    return ProjectTypeOut.model_validate(project_type)


@router.patch("/{project_type_id}")
async def update_project_type(
    project_type_id: int, body: ProjectTypeUpdate, session: SessionDep, _: Admin
) -> ProjectTypeOut:
    project_type = await existing_project_type(session, project_type_id)
    for name, value in body.model_dump(exclude_unset=True).items():
        setattr(project_type, name, value)
    await session.commit()
    return ProjectTypeOut.model_validate(project_type)


async def existing_project_type(session: AsyncSession, project_type_id: int) -> ProjectType:
    project_type = await session.get(ProjectType, project_type_id)
    if project_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project type not found.")
    return project_type
