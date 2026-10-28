"""Splits regulation pages into passages small enough to hold about one requirement each."""

import re
from collections.abc import Iterable

MAX_PASSAGE_CHARS = 1200


def split_pages(
    pages: Iterable[tuple[int, str]], max_chars: int = MAX_PASSAGE_CHARS
) -> list[tuple[int, str]]:
    """(page, text) passages: paragraphs packed up to `max_chars`, never across pages."""
    passages: list[tuple[int, str]] = []
    for page, text in pages:
        current = ""
        for paragraph in re.split(r"\n\s*\n|\n(?=\S)", text):
            paragraph = " ".join(paragraph.split())
            while len(paragraph) > max_chars:  # one huge paragraph: cut at a space
                cut = paragraph.rfind(" ", 0, max_chars)
                cut = cut if cut > 0 else max_chars
                if current:
                    passages.append((page, current))
                    current = ""
                passages.append((page, paragraph[:cut]))
                paragraph = paragraph[cut:].strip()
            if not paragraph:
                continue
            if current and len(current) + 1 + len(paragraph) > max_chars:
                passages.append((page, current))
                current = paragraph
            else:
                current = f"{current}\n{paragraph}" if current else paragraph
        if current:
            passages.append((page, current))
    return passages
