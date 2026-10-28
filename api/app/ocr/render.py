"""PDF pages as images for OCR, rendered with PDFium (pypdfium2, installed with pdfplumber)."""

import asyncio
import io
import threading

import pypdfium2 as pdfium

from app.ocr.base import OcrError

# PDFium is not thread-safe: one call at a time per process.
_PDFIUM = threading.Lock()


def _render(content: bytes, page_number: int, dpi: int) -> bytes:
    with _PDFIUM:
        document = pdfium.PdfDocument(content)
        try:
            image = document[page_number - 1].render(scale=dpi / 72).to_pil()
        finally:
            document.close()
    buffer = io.BytesIO()
    image.convert("L").save(buffer, format="PNG")  # grey is all OCR needs, and smaller
    return buffer.getvalue()


async def render_page_png(content: bytes, page_number: int, dpi: int) -> bytes:
    """Page `page_number` (1-based) as a greyscale PNG at `dpi`; 72 dpi is one pixel per point."""
    try:
        return await asyncio.to_thread(_render, content, page_number, dpi)
    except pdfium.PdfiumError as error:
        raise OcrError(f"The page could not be rendered: {error}") from error
