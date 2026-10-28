"""Synthetic PDFs for tests, written by hand so no PDF-writing dependency is needed.

Helvetica with the standard encoding: keep test text ASCII (no Romanian diacritics).
"""

import io

import pypdfium2 as pdfium


def make_pdf(*pages: list[str]) -> bytes:
    """One page per argument; each string is one line of text, from the top of an A4 page."""
    objects: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    font_id = 3
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids = []
    for lines in pages:
        commands = ["BT", "/F1 11 Tf", "14 TL", "72 770 Td"]
        for line in lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands += [f"({escaped}) Tj", "T*"]
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1")
        objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
        content_id = len(objects)
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>" % (font_id, content_id)
        )
        page_ids.append(len(objects))
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids).encode()
    objects[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(page_ids))

    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(output)
    output += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    output += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    output += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(output)


def make_scan(*pages: list[str], dpi: int = 150) -> bytes:
    """Like make_pdf, but every page is only a picture of its text, as a scanner makes it."""
    document = pdfium.PdfDocument(make_pdf(*pages))
    images = [page.render(scale=dpi / 72).to_pil().convert("L") for page in document]
    document.close()
    output = io.BytesIO()
    images[0].save(
        output, format="PDF", resolution=float(dpi), save_all=True, append_images=images[1:]
    )
    return output.getvalue()
