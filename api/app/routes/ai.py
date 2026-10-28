from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.auth import current_user
from app.deps import AIDep, SessionDep
from app.models import AiCall
from app.routes.problems import Problem

router = APIRouter(prefix="/api/ai", tags=["ai"], dependencies=[Depends(current_user)])


class AiCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    purpose: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    error: str | None


class Usage(BaseModel):
    configured: bool
    providers: list[str]
    chat_model: str
    embedding_model: str
    daily_budget_usd: float
    spent_today_usd: float
    recent_calls: list[AiCallOut]


class Ready(BaseModel):
    ready: bool


class CheckResult(BaseModel):
    chat_model: str
    chat_answer: bool
    # None when no configured account has an embeddings endpoint (Bedrock).
    embedding_model: str | None
    embedding_dimensions: int | None


@router.get("/usage")
async def usage(ai: AIDep, session: SessionDep, limit: int = Query(20, ge=1, le=100)) -> Usage:
    calls = await session.scalars(select(AiCall).order_by(AiCall.id.desc()).limit(limit))
    return Usage(
        configured=bool(ai.providers),
        providers=[provider.name for provider in ai.providers],
        chat_model=ai.chat_model,
        embedding_model=ai.settings.ai_embedding_model,
        daily_budget_usd=float(ai.settings.ai_daily_budget_usd),
        spent_today_usd=float(await ai.spent_today()),
        recent_calls=[AiCallOut.model_validate(call) for call in calls],
    )


@router.post(
    "/check",
    responses={
        429: {"model": Problem, "description": "Daily AI budget used up"},
        502: {"model": Problem, "description": "The AI provider failed"},
        503: {"model": Problem, "description": "No AI provider configured"},
    },
)
async def check(ai: AIDep) -> CheckResult:
    """One tiny structured chat call and one embedding, to prove the keys and deployments work."""
    answer = await ai.complete(
        purpose="connection check",
        messages=[{"role": "user", "content": "Set ready to true."}],
        schema=Ready,
    )
    if not ai.embedding_providers:
        return CheckResult(
            chat_model=ai.chat_model,
            chat_answer=answer.ready,
            embedding_model=None,
            embedding_dimensions=None,
        )
    vectors = await ai.embed(purpose="connection check", texts=["connection check"])
    return CheckResult(
        chat_model=ai.chat_model,
        chat_answer=answer.ready,
        embedding_model=ai.settings.ai_embedding_model,
        embedding_dimensions=len(vectors[0]),
    )
