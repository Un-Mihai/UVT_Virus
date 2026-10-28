"""Reads chosen pages of a PDF with an OCR engine, in the same coordinates as the text layer."""

import asyncio
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass

from app.ocr.base import OcrEngine, OcrError, RecognizedPage
from app.ocr.render import render_page_png
from app.pdf import Word
from app.romanian import normalize_ro


@dataclass(frozen=True)
class OcrText:
    text: str
    words: list[Word]  # PDF points from the top-left corner, with each word's confidence
    confidence: float  # mean word confidence; 0 when nothing was read


@dataclass(frozen=True)
class OcrFailure:
    error: str


def to_pdf_points(page: RecognizedPage, dpi: int) -> OcrText:
    """Pixels of a page rendered at `dpi` to PDF points (72 per inch), like pdfplumber's boxes."""
    scale = 72 / dpi
    words = [
        Word(
            normalize_ro(word.text),
            round(word.x0 * scale, 2),
            round(word.top * scale, 2),
            round(word.x1 * scale, 2),
            round(word.bottom * scale, 2),
            round(word.confidence, 3),
        )
        for word in page.words
    ]
    confidence = sum(word.confidence for word in page.words) / len(words) if words else 0.0
    return OcrText(normalize_ro(page.text), words, round(confidence, 3))


async def read_pages(
    content: bytes, page_numbers: Iterable[int], engine: OcrEngine, dpi: int, concurrency: int
) -> AsyncIterator[tuple[int, OcrText | OcrFailure]]:
    """Each page's outcome as soon as it is read, `concurrency` pages at a time."""
    limit = asyncio.Semaphore(concurrency)

    async def read(number: int) -> tuple[int, OcrText | OcrFailure]:
        async with limit:
            try:
                png = await render_page_png(content, number, dpi)
                return number, to_pdf_points(await engine.recognize(png, dpi), dpi)
            except OcrError as error:
                return number, OcrFailure(str(error))

    for done in asyncio.as_completed([read(number) for number in page_numbers]):
        yield await done
