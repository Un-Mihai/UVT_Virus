"""What an OCR engine returns, and the interface every engine implements."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RecognizedWord:
    """A word and its box in image pixels from the top-left corner; confidence from 0 to 1."""

    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    confidence: float


@dataclass(frozen=True)
class RecognizedPage:
    text: str  # lines in reading order, joined by newlines
    words: list[RecognizedWord]


@dataclass(frozen=True)
class EngineStatus:
    """What /status shows about the engine."""

    engine: str
    available: bool
    version: str | None
    languages: list[str]
    detail: str | None  # what is wrong and how to fix it, when not available


class OcrError(RuntimeError):
    """The engine could not read a page (missing binary or language, timeout, crash)."""


class OcrEngine(Protocol):
    """Adding an engine: implement this and register it in app/ocr/registry.py."""

    name: str

    async def recognize(self, png: bytes, dpi: int) -> RecognizedPage: ...

    async def probe(self) -> EngineStatus: ...
