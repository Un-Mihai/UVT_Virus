from collections.abc import Callable

from app.config import Settings
from app.ocr.base import OcrEngine
from app.ocr.tesseract import TesseractEngine

# OCR_ENGINE names an entry here. Adding an engine (a cloud service, say) is one class that
# implements OcrEngine plus one entry.
OCR_ENGINES: dict[str, Callable[[Settings], OcrEngine]] = {
    "tesseract": lambda settings: TesseractEngine(
        settings.ocr_languages, settings.ocr_timeout_seconds
    ),
}


def build_ocr_engine(settings: Settings) -> OcrEngine | None:
    """The configured engine, or None when OCR_ENGINE=none (scans are then left unread)."""
    factory = OCR_ENGINES.get(settings.ocr_engine)
    return factory(settings) if factory else None
