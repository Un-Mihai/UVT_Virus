"""PDF handling only: read text and word boxes, locate quotes, write highlight annotations."""

from app.pdf.annotate import HighlightMark, annotate_pdf
from app.pdf.locate import Rect, line_boxes, locate_quote, locate_words
from app.pdf.reader import PageContent, PdfReadError, Word, read_pdf

__all__ = [
    "HighlightMark",
    "PageContent",
    "PdfReadError",
    "Rect",
    "Word",
    "annotate_pdf",
    "line_boxes",
    "locate_quote",
    "locate_words",
    "read_pdf",
]
