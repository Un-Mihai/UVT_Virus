from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.client import AIClient
from app.auth import CurrentUser
from app.config import Settings
from app.ocr import OcrEngine
from app.personal_data import IdentifierHasher
from app.verification.orchestrator import VerificationOrchestrator
from app.verification.scope import Visibility, visibility_for


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessions() as session:
        yield session


def get_sessions(request: Request) -> async_sessionmaker[AsyncSession]:
    """The session factory itself, for background jobs that outlive the request's session."""
    sessions: async_sessionmaker[AsyncSession] = request.app.state.sessions
    return sessions


def get_ocr(request: Request) -> OcrEngine | None:
    ocr: OcrEngine | None = request.app.state.ocr
    return ocr


def get_ai(request: Request) -> AIClient:
    ai: AIClient = request.app.state.ai
    return ai


def get_settings_dep(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_hasher(request: Request) -> IdentifierHasher:
    hasher: IdentifierHasher = request.app.state.hasher
    return hasher


def get_orchestrator(request: Request) -> VerificationOrchestrator:
    orchestrator: VerificationOrchestrator = request.app.state.orchestrator
    return orchestrator


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SessionsDep = Annotated[async_sessionmaker[AsyncSession], Depends(get_sessions)]
OcrDep = Annotated[OcrEngine | None, Depends(get_ocr)]
AIDep = Annotated[AIClient, Depends(get_ai)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
HasherDep = Annotated[IdentifierHasher, Depends(get_hasher)]
OrchestratorDep = Annotated[VerificationOrchestrator, Depends(get_orchestrator)]


def get_visibility(user: CurrentUser, settings: SettingsDep) -> Visibility:
    """The caller's verification scope and confidence threshold; 403 for roles without one."""
    visibility = visibility_for(user, settings)
    if visibility is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only clients and reviewers verify projects."
        )
    return visibility


VisibilityDep = Annotated[Visibility, Depends(get_visibility)]
