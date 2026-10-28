"""OCR for pages without a text layer. Knows nothing about the database or HTTP."""

from app.ocr.base import EngineStatus, OcrEngine, OcrError, RecognizedPage, RecognizedWord
from app.ocr.pages import OcrFailure, OcrText, read_pages
from app.ocr.registry import build_ocr_engine

__all__ = [
    "EngineStatus",
    "OcrEngine",
    "OcrError",
    "OcrFailure",
    "OcrText",
    "RecognizedPage",
    "RecognizedWord",
    "build_ocr_engine",
    "read_pages",
]
