import io
from dataclasses import dataclass
from typing import Any

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

from app.romanian import normalize_ro

DIAGONAL_EPSILON = 0.05  # of a text matrix entry: rotation by about 3 degrees or more


class PdfReadError(ValueError):
    pass


@dataclass(frozen=True)
class Word:
    """A word and its box in PDF points, measured from the page's top-left corner."""

    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    # 0 to 1 when the word was read by OCR; None when it comes from the PDF's text layer.
    confidence: float | None = None


@dataclass(frozen=True)
class PageContent:
    number: int  # 1-based
    text: str
    width: float
    height: float
    words: list[Word]

    @property
    def is_scan(self) -> bool:
        """No text layer: the page is an image, read by OCR (app/ocr) after upload."""
        return not self.words


def _is_diagonal(char: dict[str, Any]) -> bool:
    """Set at an angle that is no multiple of 90 degrees: a SPECIMEN or TEST watermark, whose
    letters would otherwise land inside the words of the real text. Slanted (italic) text keeps
    one axis straight and rotated text keeps both, so neither counts."""
    a, b, c, d = (abs(value) for value in char["matrix"][:4])
    return bool(min(a, b, c, d) > DIAGONAL_EPSILON)


def read_pdf(content: bytes) -> list[PageContent]:
    """Text and word boxes per page, with Romanian diacritics normalised and watermarks left
    out."""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [
                page.filter(lambda item: item["object_type"] != "char" or not _is_diagonal(item))
                for page in pdf.pages
            ]
            return [
                PageContent(
                    number=index,
                    text=normalize_ro(page.extract_text() or ""),
                    width=float(page.width),
                    height=float(page.height),
                    words=[
                        Word(
                            normalize_ro(word["text"]),
                            float(word["x0"]),
                            float(word["top"]),
                            float(word["x1"]),
                            float(word["bottom"]),
                        )
                        for word in page.extract_words()
                    ],
                )
                for index, page in enumerate(pages, start=1)
            ]
    except PdfminerException as error:
        raise PdfReadError("The file is not a readable PDF.") from error
