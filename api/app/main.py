from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
import openai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.ai.client import AIClient, AINotConfiguredError, AIResponseError, BudgetExceededError
from app.auth import TokenVerifier
from app.config import Settings, get_settings
from app.routes import ai, health, me


def create_app(
    settings: Settings | None = None,
    ai_http: httpx2.AsyncClient | None = None,
    auth: TokenVerifier | None = None,
) -> FastAPI:
    """`ai_http` and `auth` let tests answer AI requests and sign tokens without a network."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        app.state.sessions = sessions
        app.state.ai = AIClient(settings, sessions, ai_http)
        app.state.auth = auth or TokenVerifier(
            settings.auth_issuer, settings.auth_audience, settings.auth_jwks_url
        )
        yield
        await app.state.ai.close()
        await engine.dispose()

    app = FastAPI(title="Hackathon API", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(ai.router)

    @app.exception_handler(AINotConfiguredError)
    async def not_configured(_: Request, error: AINotConfiguredError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=503)

    @app.exception_handler(BudgetExceededError)
    async def over_budget(_: Request, error: BudgetExceededError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=429)

    @app.exception_handler(AIResponseError)
    async def bad_answer(_: Request, error: AIResponseError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=502)

    @app.exception_handler(openai.APIError)
    async def provider_error(_: Request, error: openai.APIError) -> JSONResponse:
        return JSONResponse({"detail": f"AI provider error: {error.message}"}, status_code=502)

    return app


app = create_app()
