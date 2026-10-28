from dataclasses import dataclass
from decimal import Decimal

from app.localized import LocalizedText
from app.pdf import Rect
from app.vocabulary import Severity

CERTAIN = Decimal(1)


@dataclass(frozen=True)
class Evidence:
    document_id: int
    page: int
    quote: str  # what people are shown
    # What to highlight when it differs from `quote` (a CNP is shown masked, found in clear).
    locate: str | None = None


@dataclass(frozen=True)
class RegulationRef:
    """The regulation passage a finding rests on."""

    document_id: int  # RegulationDocument.id
    page: int
    quote: str | None  # the passage's own words, when the model quoted them exactly


@dataclass(frozen=True)
class FindingDraft:
    """What an agent reports; the orchestrator adds highlight boxes and stores it."""

    rule_code: str
    agent: str
    severity: Severity
    confidence: Decimal
    reason: LocalizedText
    recommendation: LocalizedText
    evidence: Evidence | None = None  # None: about the form, or about something missing
    regulation: RegulationRef | None = None  # None: an admin's written rule, or no regulation


@dataclass(frozen=True)
class ResolvedFinding:
    draft: FindingDraft
    rects: list[Rect]
    confidence: Decimal  # the draft's, capped by OCR confidence when the evidence was OCR'd
    ocr: bool
