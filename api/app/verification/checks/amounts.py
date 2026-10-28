"""Sums inside one document, computed with Decimal from the values as written."""

from decimal import Decimal

from pydantic import BaseModel

from app.romanian import parse_ro_amount
from app.verification.checks.common import finding
from app.verification.checks.registry import register_check
from app.verification.context import DocumentView, RuleView, VerificationContext
from app.verification.facts import ExtractedAmount
from app.verification.findings import Evidence, FindingDraft


class SumParams(BaseModel):
    tolerance: str = "0.01"  # rounding allowed, in the document's currency


@register_check(
    "amounts.totals_add_up",
    {
        "en": "Line totals add up to the subtotal, and subtotal plus VAT equals the grand total.",
        "ro": "Totalurile pe linii dau subtotalul, iar subtotalul plus TVA dă totalul general.",
    },
    SumParams,
)
def totals_add_up(
    context: VerificationContext, rule: RuleView, params: SumParams
) -> list[FindingDraft]:
    tolerance = Decimal(params.tolerance)
    findings = []
    for document in context.documents:
        located = _amounts_by_kind(document)
        lines = located.get("line_total", [])
        subtotal = _single(located.get("subtotal", []))
        vat = _single(located.get("vat", []))
        grand = _single(located.get("grand_total", []))
        if lines and subtotal:
            expected = sum((value for value, _, _ in lines), Decimal(0))
            if abs(expected - subtotal[0]) > tolerance:
                findings.append(_mismatch(rule, "subtotal_mismatch", document, subtotal, expected))
        if subtotal and vat and grand:
            expected = subtotal[0] + vat[0]
            if abs(expected - grand[0]) > tolerance:
                findings.append(_mismatch(rule, "grand_total_mismatch", document, grand, expected))
    return findings


type Located = tuple[Decimal, int, ExtractedAmount]  # value, page, fact


def _amounts_by_kind(document: DocumentView) -> dict[str, list[Located]]:
    found: dict[str, list[Located]] = {}
    for page in document.pages:
        for amount in page.facts.amounts if page.facts else []:
            value = parse_ro_amount(amount.value)
            if value is not None:
                found.setdefault(amount.kind, []).append((value, page.number, amount))
    return found


def _single(amounts: list[Located]) -> Located | None:
    # shortcut: documents with several subtotals (one per section) are skipped; group lines by
    # section when the demo files need it.
    return amounts[0] if len(amounts) == 1 else None


def _mismatch(
    rule: RuleView, key: str, document: DocumentView, stated: Located, expected: Decimal
) -> FindingDraft:
    _, page, fact = stated
    return finding(
        rule,
        key,
        Evidence(document.id, page, fact.quote, locate=fact.value),
        label=fact.label,
        document=document.filename,
        stated=fact.value,
        expected=expected,
    )
