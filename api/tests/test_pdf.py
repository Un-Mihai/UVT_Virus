import io
from typing import Any

import pytest
from pypdf import PdfReader
from pypdf.generic import ArrayObject

from app.pdf import HighlightMark, PdfReadError, annotate_pdf, locate_quote, read_pdf
from app.pdf.reader import _is_diagonal
from tests.pdf_factory import make_pdf

PDF = make_pdf(
    ["Contract de finantare nr. 12", "Valoarea garan-", "tiei de buna executie este 10%"],
    ["Second page"],
)


def test_reads_text_and_word_boxes_per_page() -> None:
    first, second = read_pdf(PDF)

    assert (first.number, first.width, first.height) == (1, 595, 842)
    assert "Contract de finantare" in first.text
    assert first.words[0].text == "Contract"
    assert first.words[0].top < first.words[-1].top  # measured from the top
    assert second.text == "Second page"
    assert not first.is_scan


def test_a_diagonal_watermark_is_not_part_of_the_page_text() -> None:
    [page] = read_pdf(
        make_pdf(["Semnatura emitentului", "Contract de finantare"], watermark="SPECIMEN")
    )

    assert page.text == "Semnatura emitentului\nContract de finantare"
    assert [word.text for word in page.words] == [
        "Semnatura",
        "emitentului",
        "Contract",
        "de",
        "finantare",
    ]


def test_only_text_rotated_off_the_axes_counts_as_diagonal() -> None:
    def char(*matrix: float) -> dict[str, Any]:
        return {"matrix": matrix}

    assert _is_diagonal(char(0.82, 0.57, -0.57, 0.82, 0, 0))
    assert not _is_diagonal(char(1, 0, 0, 1, 0, 0))  # upright
    assert not _is_diagonal(char(0, 1, -1, 0, 0, 0))  # a vertical label
    assert not _is_diagonal(char(1, 0, 0.2, 1, 0, 0))  # italic slant


def test_rejects_files_that_are_not_pdfs() -> None:
    with pytest.raises(PdfReadError):
        read_pdf(b"%PDF-1.4 but broken")


def test_locates_a_quote_across_a_hyphenated_line_break() -> None:
    words = read_pdf(PDF)[0].words

    rects = locate_quote(words, "garantiei de buna executie")

    assert rects is not None
    assert len(rects) == 2  # one box per line
    assert rects[0][1] < rects[1][1]
    assert locate_quote(words, "garantia de participare") is None
    assert locate_quote(words, "  ") is None


def test_annotates_highlights_with_their_anchor() -> None:
    rects = locate_quote(read_pdf(PDF)[0].words, "Contract de finantare")
    assert rects

    annotated = annotate_pdf(PDF, [HighlightMark(1, rects, "finding-7", "Why", "f28b82")])

    annotation = annotations_of(annotated)[0]
    assert annotation["/Subtype"] == "/Highlight"
    assert annotation["/NM"] == "finding-7"
    assert annotation["/Contents"] == "Why"
    top_edge = float(annotation["/Rect"][3])
    # 842 - top: the box sits near the top of the page in PDF coordinates.
    assert top_edge == pytest.approx(842 - rects[0][1])


def annotations_of(pdf: bytes, page: int = 0) -> list[Any]:
    """The annotation dictionaries on one page of a PDF."""
    annotations = PdfReader(io.BytesIO(pdf)).pages[page]["/Annots"]
    assert isinstance(annotations, ArrayObject)
    return [annotation.get_object() for annotation in annotations]
