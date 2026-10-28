import io
from collections.abc import Sequence
from dataclasses import dataclass

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Highlight
from pypdf.generic import ArrayObject, FloatObject, NameObject, TextStringObject

from app.pdf.locate import Rect


@dataclass(frozen=True)
class HighlightMark:
    page: int  # 1-based
    rects: Sequence[Rect]
    anchor: str  # "finding-{id}"; stored as the annotation's /NM so viewers can find it
    note: str  # the reason and recommendation, shown in the annotation popup
    color: str  # hex RGB, e.g. "f5c542"


def annotate_pdf(content: bytes, marks: Sequence[HighlightMark]) -> bytes:
    """A copy of the PDF with one Highlight annotation per mark; the original is untouched."""
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(content)))
    for mark in marks:
        if not mark.rects:
            continue
        page = writer.pages[mark.page - 1]
        bottom, height = float(page.mediabox.bottom), float(page.mediabox.height)
        # Boxes are measured from the top-left; PDF coordinates start bottom-left.
        boxes = [
            (x0, bottom + height - lower, x1, bottom + height - upper)
            for x0, upper, x1, lower in mark.rects
        ]
        quads = ArrayObject(
            FloatObject(value)
            for x0, y0, x1, y1 in boxes
            for value in (x0, y1, x1, y1, x0, y0, x1, y0)
        )
        annotation = Highlight(
            rect=(
                min(box[0] for box in boxes),
                min(box[1] for box in boxes),
                max(box[2] for box in boxes),
                max(box[3] for box in boxes),
            ),
            quad_points=quads,
            highlight_color=mark.color,
            printing=True,
        )
        annotation[NameObject("/NM")] = TextStringObject(mark.anchor)
        annotation[NameObject("/Contents")] = TextStringObject(mark.note)
        writer.add_annotation(page_number=mark.page - 1, annotation=annotation)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
