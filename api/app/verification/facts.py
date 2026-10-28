"""Facts the extraction agent reads from a page. Checks consume them; the model never computes.

Plain schemas (no Field constraints) so Azure's strict structured output accepts them. Values
are text exactly as written; checks parse them with app.romanian.
"""

from pydantic import BaseModel

DOCUMENT_TYPES = (
    "financing_application",
    "contract",
    "offer",
    "invoice",
    "budget",
    "guarantee",
    "certificate",
    "statement",
    "other",
)
AMOUNT_KINDS = ("line_total", "subtotal", "vat", "grand_total", "other")


class ExtractedParty(BaseModel):
    name: str
    cui: str | None  # as written, with or without "RO"
    role: str | None  # "beneficiary", "supplier", "contracting authority"...
    quote: str


class ExtractedValue(BaseModel):
    label: str  # the label on the page, e.g. "Data facturii"
    value: str  # exactly as written
    quote: str


class ExtractedAmount(BaseModel):
    label: str
    value: str  # exactly as written, e.g. "1.234.567,89"
    currency: str | None
    kind: str  # one of AMOUNT_KINDS
    quote: str


class PageFacts(BaseModel):
    document_type: str | None  # one of DOCUMENT_TYPES
    parties: list[ExtractedParty]
    ibans: list[ExtractedValue]
    amounts: list[ExtractedAmount]
    dates: list[ExtractedValue]
