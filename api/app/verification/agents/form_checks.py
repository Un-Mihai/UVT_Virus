"""Reads the boxes people tick on forms and reports the contradictions a model skims over.

Deterministic and always on: no model call, no cost, no regulation passage needed. It reports
two options that exclude each other both ticked, a consent answered "NU", a consent list ticked
only in part, an income certificate older than the validity it states for itself, an identity
card that expired before the application, loan instalments paid in a statement that the
application does not declare, an ANAF income well under the declared one, and a CNP whose
check digit is wrong.
"""

import collections
import itertools
import re
from datetime import date
from decimal import Decimal

from app.localized import LocalizedText
from app.romanian import parse_ro_amount, parse_ro_date
from app.verification.checks import run_check
from app.verification.context import DocumentView, RuleView, VerificationContext
from app.verification.findings import CERTAIN, Evidence, FindingDraft
from app.verification.messages import Param, message
from app.vocabulary import Severity

OPTION = re.compile(r"([☒☐])\s*([^☒☐]+)")
CONSENT_REFUSED = re.compile(r"☐\s*DA\s*☒\s*NU\s+sunt de acord", re.IGNORECASE)
LIST_ITEM = re.compile(r"^\s*(?:\d+\.\s+)?(X\s+)?([a-z]\)\s+\S.*?)\s*$")
ISSUED = re.compile(r"Data emiterii:\s*(\d{1,2}\.\d{1,2}\.\d{4})")
VALID_DAYS = re.compile(
    r"valabil[ăa]\s+(\d+)\s+(?:de\s+)?zile\s+de\s+la\s+data\s+emiterii", re.IGNORECASE
)
APPLIED = re.compile(r"CERERE DE CREDIT.{0,200}?din data de\s+(\d{1,2}\.\d{1,2}\.\d{4})", re.DOTALL)
TRAILING_NUMBER = re.compile(r"\s+\d+\s*$")
ID_HEADER = re.compile(r"Eliberat.*Valabil\s+până\s+la", re.IGNORECASE)
DATE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
DECLARED_HEADER = re.compile(r"Total rate lunare", re.IGNORECASE)
RO_AMOUNT = re.compile(r"\d[\d.]*,\d{2}")
PAID_INSTALMENT = re.compile(
    r"^\d{2}\.(\d{2})\.(\d{4})\s+\d{2}\.\d{2}\.\d{4}\s+Plat[ăa]\s+rat[ăa]\b.*?(\d[\d ]*[.,]\d{2})$",
    re.IGNORECASE,
)
PAYEE = re.compile(r"Beneficiar:\s*([^|]+?)\s*(?:\|.*?Contract nr\.?\s*(\S+))?$", re.IGNORECASE)
INCOME_ROW = re.compile(r"venit realizat\s+(\d+)\s+(\d+)\s+(\d+)", re.IGNORECASE)
D112_DATE = re.compile(
    r"Declara[țt]ia\s+112.*?din data de\s+(\d{2}\.\d{2}\.\d{4})", re.DOTALL | re.IGNORECASE
)
DECLARED_INCOME = re.compile(r"Salariu net lunar.*Venit net mediu", re.IGNORECASE)
HIRED = re.compile(r"Data angajării", re.IGNORECASE)


CNP_RULE = RuleView("personal_data.cnp_valid", "CNP", "", Severity.BAD)


class FormChecksAgent:
    name = "forms"

    async def run(self, context: VerificationContext) -> list[FindingDraft]:
        # The CNP check digit is arithmetic too: it runs every time, not only when the model asks.
        # The orchestrator keeps one copy when the model asks for it as well.
        cnp = run_check(context, CNP_RULE, CNP_RULE.code, {})
        return form_findings(context.documents) + cnp


def form_findings(documents: list[DocumentView]) -> list[FindingDraft]:
    applied = _application_date(documents)
    drafts = []
    for document in documents:
        for page in document.pages:
            for line in page.text.splitlines():
                drafts += _conflicting_marks(document, page.number, line)
                if refused := CONSENT_REFUSED.search(line):
                    drafts.append(
                        _draft("consent_refused", document, page.number, refused.group(), "refused")
                    )
            drafts += _partial_consent(document, page.number, page.text)
        drafts += _expired_certificate(document, applied)
    return (
        drafts
        + _expired_id_card(documents, applied)
        + _undeclared_instalments(documents)
        + _income_below_declared(documents)
    )


def _draft(
    code: str,
    document: DocumentView,
    page: int,
    quote: str,
    key: str,
    *,
    locate: str | None = None,
    **params: Param,
) -> FindingDraft:
    reason, recommendation = message(f"form_{key}", document=document.filename, **params)
    return FindingDraft(
        rule_code=f"forms.{code}",
        agent="forms",
        severity=Severity.BAD,
        confidence=CERTAIN,
        reason=reason,
        recommendation=recommendation,
        evidence=Evidence(document.id, page, quote, locate),
    )


def _conflicting_marks(document: DocumentView, page: int, line: str) -> list[FindingDraft]:
    """Two neighbouring options both ticked, like "☒ necăsătorit(ă) ☒ căsătorit(ă)".

    Neighbours only: a line may hold several independent questions, one answer each.
    """
    # shortcut: a group that wraps onto the next line is compared line by line, so a pair
    # ticked across the break is missed. Compare across lines if such forms turn up.
    options = list(OPTION.finditer(line))
    drafts = []
    for first, second in itertools.pairwise(options):
        if first.group(1) == "☒" and second.group(1) == "☒":
            quote = TRAILING_NUMBER.sub("", line[first.start() : second.end()]).strip()
            labels = {
                name: TRAILING_NUMBER.sub("", option.group(2)).strip()
                for name, option in (("first", first), ("second", second))
            }
            drafts.append(_draft("conflicting_marks", document, page, quote, "marks", **labels))
    return drafts


def _partial_consent(document: DocumentView, page: int, text: str) -> list[FindingDraft]:
    """On a consent form, a list of items with some ticked "X" and some not."""
    if "ACORD DE CONSULTARE" not in text.upper():
        return []
    items = [m for line in text.splitlines() if (m := LIST_ITEM.match(line))]
    if not any(m.group(1) for m in items):
        return []
    return [
        _draft("consent_incomplete", document, page, m.group(2), "incomplete", item=m.group(2))
        for m in items
        if not m.group(1)
    ]


def _application_date(documents: list[DocumentView]) -> date | None:
    for document in documents:
        for page in document.pages:
            if found := APPLIED.search(page.text):
                return parse_ro_date(found.group(1))
    return None


def _expired_certificate(document: DocumentView, applied: date | None) -> list[FindingDraft]:
    """A certificate that says "valabilă N zile de la data emiterii", older than that when the
    application was made. The validity is read from the certificate, not assumed."""
    if applied is None:
        return []
    text = "\n".join(page.text for page in document.pages)
    valid = VALID_DAYS.search(text)
    for page in document.pages:
        issued = ISSUED.search(page.text)
        when = parse_ro_date(issued.group(1)) if issued else None
        if issued and when and valid and (age := (applied - when).days) > int(valid.group(1)):
            return [
                _draft(
                    "certificate_expired",
                    document,
                    page.number,
                    issued.group(),
                    "expired",
                    issued=issued.group(1),
                    applied=applied.strftime("%d.%m.%Y"),
                    age=_days(age),
                    valid=_days(int(valid.group(1))),
                )
            ]
    return []


def _days(count: int) -> LocalizedText:
    """Romanian takes "de" from 20 up, except for 01 to 19 in the
    last two digits (21 de zile, 111 zile)."""
    ro = "1 zi" if count == 1 else f"{count} zile" if 0 < count % 100 < 20 else f"{count} de zile"
    return {"en": f"{count} day{'' if count == 1 else 's'}", "ro": ro}


def _following(lines: list[str], index: int) -> str | None:
    return next((line.strip() for line in lines[index + 1 :] if line.strip()), None)


def _expired_id_card(documents: list[DocumentView], applied: date | None) -> list[FindingDraft]:
    """The identity card's "Valabil până la" falls before the date of the application. The
    application and the KYC form both repeat the card's data: one finding per expiry date."""
    drafts: list[FindingDraft] = []
    seen: set[date] = set()
    for document in documents:
        for page in document.pages:
            lines = page.text.splitlines()
            for index, line in enumerate(lines):
                values = _following(lines, index) if ID_HEADER.search(line) else None
                dates = DATE.findall(values or "")
                expiry = parse_ro_date(dates[-1]) if dates else None
                if values and applied and expiry and expiry < applied and expiry not in seen:
                    seen.add(expiry)
                    drafts.append(
                        _draft(
                            "id_expired",
                            document,
                            page.number,
                            values,
                            "id_expired",
                            locate=dates[-1],
                            expiry=dates[-1],
                            applied=applied.strftime("%d.%m.%Y"),
                        )
                    )
    return drafts


def _declared_instalments(documents: list[DocumentView]) -> Decimal | None:
    """The "Total rate lunare existente declarate" of the application."""
    for document in documents:
        for page in document.pages:
            lines = page.text.splitlines()
            for index, line in enumerate(lines):
                if DECLARED_HEADER.search(line):
                    found = RO_AMOUNT.search(_following(lines, index) or "")
                    return parse_ro_amount(found.group()) if found else None
    return None


def _undeclared_instalments(documents: list[DocumentView]) -> list[FindingDraft]:
    """Loan instalments paid month after month in a statement, beyond the total the application
    declares. A payment counts as an instalment when the same payee gets it in two months."""
    declared = _declared_instalments(documents)
    if declared is None:
        return []
    paid: dict[tuple[str, str], list[tuple[tuple[str, str], Decimal]]] = collections.defaultdict(
        list
    )
    first: dict[tuple[str, str], tuple[DocumentView, int, str]] = {}
    for document in documents:
        for page in document.pages:
            lines = [line.strip() for line in page.text.splitlines()]
            for index, line in enumerate(lines):
                payment = PAID_INSTALMENT.match(line)
                amount = parse_ro_amount(payment.group(3)) if payment else None
                if not (payment and amount):
                    continue
                payee = PAYEE.match(lines[index + 1]) if index + 1 < len(lines) else None
                key = (payee.group(1), payee.group(2) or "") if payee else ("", "")
                paid[key].append(((payment.group(2), payment.group(1)), amount))
                first.setdefault(key, (document, page.number, line))
    monthly = {
        key: collections.Counter(amount for _, amount in rows).most_common(1)[0][0]
        for key, rows in paid.items()
        if len({month for month, _ in rows}) >= 2
    }
    total = sum(monthly.values(), Decimal(0))
    if not monthly or total <= declared:
        return []
    where, number, quote = first[next(iter(monthly))]
    creditors = ", ".join(sorted({name for name, _ in monthly if name})) or "?"
    return [
        _draft(
            "installment_undeclared",
            where,
            number,
            quote,
            "installments",
            declared=declared,
            found=total,
            creditor=creditors,
        )
    ]


def _income_below_declared(documents: list[DocumentView]) -> list[FindingDraft]:
    """The net income an ANAF certificate shows per month is well under the average the
    application declares. The certificate has one row for the year so far: taxable income less
    tax, over the months before its last D112 (counted from the hiring month when the job
    started that year). Under 80% of the declared average is reported."""
    declared: Decimal | None = None
    hired: date | None = None
    for document in documents:
        for page in document.pages:
            lines = page.text.splitlines()
            for index, line in enumerate(lines):
                if DECLARED_INCOME.search(line):
                    amounts = RO_AMOUNT.findall(_following(lines, index) or "")
                    declared = parse_ro_amount(amounts[1]) if len(amounts) > 1 else None
                elif HIRED.search(line):
                    found = DATE.search(_following(lines, index) or "")
                    hired = parse_ro_date(found.group()) if found else None
    if declared is None:
        return []
    drafts = []
    for document in documents:
        for page in document.pages:
            row, filed = INCOME_ROW.search(page.text), D112_DATE.search(page.text)
            last_d112 = parse_ro_date(filed.group(1)) if filed else None
            if not (row and last_d112):
                continue
            months = last_d112.month - 1
            if hired and hired.year == last_d112.year:
                months -= hired.month
            net = Decimal(int(row.group(2)) - int(row.group(3)))
            monthly = (net / months).quantize(Decimal(1)) if months > 0 else None
            if monthly is not None and monthly < declared * Decimal("0.8"):
                quote = next(
                    (x.strip() for x in page.text.splitlines() if INCOME_ROW.search(x)), ""
                )
                drafts.append(
                    _draft(
                        "income_below_declared",
                        document,
                        page.number,
                        quote or row.group(),
                        "income",
                        locate=row.group(),
                        anaf=monthly,
                        declared=declared,
                        months=months,
                    )
                )
    return drafts
