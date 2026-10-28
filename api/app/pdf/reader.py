import io
from dataclasses import dataclass

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

from app.romanian import normalize_ro


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


def read_pdf(content: bytes) -> list[PageContent]:
    """Text and word boxes per page, with Romanian diacritics normalised."""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
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
                for index, page in enumerate(pdf.pages, start=1)
            ]
    except PdfminerException as error:
        raise PdfReadError("The file is not a readable PDF.") from error
