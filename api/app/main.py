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
from app.documents.ingest import UploadRejectedError
from app.ocr import OcrEngine, build_ocr_engine
from app.personal_data import IdentifierHasher
from app.routes import (
    ai,
    findings,
    health,
    me,
    ocr_status,
    project_types,
    projects,
    regulations,
    required_documents,
    verifications,
)
from app.verification.orchestrator import default_orchestrator


def create_app(
    settings: Settings | None = None,
    ai_http: httpx2.AsyncClient | None = None,
    auth: TokenVerifier | None = None,
    ocr: OcrEngine | None = None,
) -> FastAPI:
    """`ai_http`, `auth` and `ocr` let tests answer AI requests, sign tokens and read scans
    without a network or a Tesseract binary; otherwise `ocr` follows OCR_ENGINE."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        app.state.sessions = sessions
        app.state.ai = AIClient(settings, sessions, ai_http)
        app.state.orchestrator = default_orchestrator(app.state.ai, settings)
        app.state.auth = auth or TokenVerifier(
            settings.auth_issuer, settings.auth_audience, settings.auth_jwks_url
        )
        yield
        await app.state.ai.close()
        await engine.dispose()

    app = FastAPI(title="Hackathon API", lifespan=lifespan)
    app.state.settings = settings
    app.state.hasher = IdentifierHasher(settings.personal_data_hash_key)
    app.state.ocr = ocr or build_ocr_engine(settings)
    for module in (
        health,
        me,
        ai,
        ocr_status,
        project_types,
        regulations,
        projects,
        required_documents,
        verifications,
        findings,
    ):
        app.include_router(module.router)

    @app.exception_handler(AINotConfiguredError)
    async def not_configured(_: Request, error: AINotConfiguredError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=503)

    @app.exception_handler(BudgetExceededError)
    async def over_budget(_: Request, error: BudgetExceededError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=429)

    @app.exception_handler(AIResponseError)
    async def bad_answer(_: Request, error: AIResponseError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=502)

    @app.exception_handler(UploadRejectedError)
    async def upload_rejected(_: Request, error: UploadRejectedError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=error.status_code)

    @app.exception_handler(openai.APIError)
    async def provider_error(_: Request, error: openai.APIError) -> JSONResponse:
        return JSONResponse({"detail": f"AI provider error: {error.message}"}, status_code=502)

    return app


app = create_app()
