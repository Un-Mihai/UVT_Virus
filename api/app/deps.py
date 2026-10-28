from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import AIClient


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessions() as session:
        yield session


def get_ai(request: Request) -> AIClient:
    ai: AIClient = request.app.state.ai
    return ai


SessionDep = Annotated[AsyncSession, Depends(get_session)]
AIDep = Annotated[AIClient, Depends(get_ai)]
