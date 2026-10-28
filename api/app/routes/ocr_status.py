from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import current_user
from app.deps import OcrDep

router = APIRouter(prefix="/api/ocr", tags=["ocr"], dependencies=[Depends(current_user)])


class OcrStatusOut(BaseModel):
    engine: str
    available: bool
    version: str | None
    languages: list[str]
    detail: str | None  # what is wrong and how to fix it, when not available


@router.get("/status")
async def ocr_status(ocr: OcrDep) -> OcrStatusOut:
    """Whether scanned pages can be read, for the status page."""
    if ocr is None:
        return OcrStatusOut(
            engine="none",
            available=False,
            version=None,
            languages=[],
            detail="Set OCR_ENGINE=tesseract in .env to read scanned pages, then restart the API.",
        )
    status = await ocr.probe()
    return OcrStatusOut(
        engine=status.engine,
        available=status.available,
        version=status.version,
        languages=status.languages,
        detail=status.detail,
    )
