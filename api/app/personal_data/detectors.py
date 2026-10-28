"""Finds personal identifiers in text. Add a kind by adding a Detector to DETECTORS."""

import re
from dataclasses import dataclass
from typing import Protocol

from app.romanian import is_valid_cnp


@dataclass(frozen=True)
class Detection:
    kind: str
    start: int
    end: int
    value: str
    valid: bool


class Detector(Protocol):
    kind: str

    def find(self, text: str) -> list[Detection]: ...


class CnpDetector:
    """Valid 13-digit CNPs anywhere, and invalid ones only when labelled "CNP" just before."""

    kind = "cnp"
    _candidate = re.compile(r"(?<!\d)[1-9]\d{12}(?!\d)")
    _label = re.compile(r"\bC\.?\s?N\.?\s?P\.?\b[^\d\n]{0,20}$", re.IGNORECASE)

    def find(self, text: str) -> list[Detection]:
        found = []
        for match in self._candidate.finditer(text):
            value = match.group()
            valid = is_valid_cnp(value)
            if valid or self._label.search(text[max(0, match.start() - 30) : match.start()]):
                found.append(Detection(self.kind, match.start(), match.end(), value, valid))
        return found


DETECTORS: tuple[Detector, ...] = (CnpDetector(),)


def detect_all(text: str, detectors: tuple[Detector, ...] = DETECTORS) -> list[Detection]:
    """Every detection, in text order, without overlaps (the first detector wins)."""
    found = sorted(
        (detection for detector in detectors for detection in detector.find(text)),
        key=lambda detection: detection.start,
    )
    kept: list[Detection] = []
    for detection in found:
        if not kept or detection.start >= kept[-1].end:
            kept.append(detection)
    return kept
