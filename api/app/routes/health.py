from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import SessionDep

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str
    database: str
    pgvector: str | None


@router.get("/health/live")
async def live() -> dict[str, str]:
    """Liveness: the process answers. Does not touch the database."""
    return {"status": "ok"}


@router.get("/health", response_model=Health, responses={503: {"model": Health}})
async def health(session: SessionDep) -> Health | JSONResponse:
    """Readiness: the database answers and has pgvector installed."""
    try:
        pgvector = await session.scalar(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
    except (SQLAlchemyError, OSError):
        down = Health(status="degraded", database="unreachable", pgvector=None)
        return JSONResponse(down.model_dump(), status_code=503)
    return Health(status="ok", database="ok", pgvector=pgvector)
