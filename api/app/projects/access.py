"""Who may see and change a project. Routes call these instead of checking roles themselves."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Role, User
from app.models import Project
from app.vocabulary import ProjectStatus


def can_view(user: User, project: Project) -> bool:
    """Clients see their own projects; reviewers see the ones clients submitted."""
    if user.has_role(Role.CLIENT) and project.owner_id == user.id:
        return True
    return user.has_role(Role.REVIEWER) and project.status == ProjectStatus.SUBMITTED


def can_edit(user: User, project: Project) -> bool:
    return (
        user.has_role(Role.CLIENT)
        and project.owner_id == user.id
        and project.status == ProjectStatus.DRAFT
    )


async def visible_project(session: AsyncSession, user: User, project_id: int) -> Project:
    """The project, or 404 also when it exists but is not the user's to see (no probing)."""
    project = await session.get(Project, project_id)
    if project is None or not can_view(user, project):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    return project


async def editable_project(session: AsyncSession, user: User, project_id: int) -> Project:
    project = await visible_project(session, user, project_id)
    if not can_edit(user, project):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Only the owner can change a project, and only before it is submitted.",
        )
    return project
