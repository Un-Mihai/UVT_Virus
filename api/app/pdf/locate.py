"""Finds a quote among a page's words, for highlight boxes and the words' OCR confidence."""

from collections.abc import Sequence

from app.pdf.reader import Word
from app.romanian import normalize_ro

type Rect = tuple[float, float, float, float]  # x0, top, x1, bottom in PDF points


def _key(text: str) -> str:
    # Letters and digits only: spacing, punctuation and line-end hyphens differ between the
    # model's quote and the PDF's text layer.
    return "".join(char for char in normalize_ro(text).casefold() if char.isalnum())


def locate_words(words: Sequence[Word], quote: str) -> list[Word] | None:
    """The words making up the quote's first occurrence on the page, or None."""
    needle = _key(quote)
    if not needle:
        return None
    stream: list[str] = []
    owner: list[int] = []  # word index of each character in `stream`
    for index, word in enumerate(words):
        key = _key(word.text)
        stream.append(key)
        owner += [index] * len(key)
    start = "".join(stream).find(needle)
    if start < 0:
        return None
    return [words[index] for index in sorted(set(owner[start : start + len(needle)]))]


def line_boxes(words: Sequence[Word]) -> list[Rect]:
    """One box per line the words span."""
    lines: list[list[Word]] = []
    for word in words:
        if lines and abs(lines[-1][0].top - word.top) < (word.bottom - word.top) / 2:
            lines[-1].append(word)
        else:
            lines.append([word])
    return [
        (
            round(min(w.x0 for w in line), 2),
            round(min(w.top for w in line), 2),
            round(max(w.x1 for w in line), 2),
            round(max(w.bottom for w in line), 2),
        )
        for line in lines
    ]


def locate_quote(words: Sequence[Word], quote: str) -> list[Rect] | None:
    """One box per line the quote spans, at its first occurrence on the page."""
    matched = locate_words(words, quote)
    return line_boxes(matched) if matched else None
