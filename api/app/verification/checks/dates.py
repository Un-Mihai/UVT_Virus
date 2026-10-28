from pydantic import BaseModel

from app.romanian import normalize_ro, parse_ro_date
from app.verification.checks.common import finding
from app.verification.checks.registry import register_check
from app.verification.context import RuleView, VerificationContext
from app.verification.findings import Evidence, FindingDraft


class PeriodParams(BaseModel):
    # Which dates to check, by a word in their label on the page, e.g. "factur" for invoices.
    label_contains: str


@register_check(
    "dates.within_project_period",
    {
        "en": "Dates whose label contains the given text fall between the form's start and end"
        " dates.",
        "ro": "Datele a căror etichetă conține textul dat se încadrează între datele de început"
        " și de sfârșit din cerere.",
    },
    PeriodParams,
)
def within_project_period(
    context: VerificationContext, rule: RuleView, params: PeriodParams
) -> list[FindingDraft]:
    start = parse_ro_date(context.form.get("start_date") or "")
    end = parse_ro_date(context.form.get("end_date") or "")
    if not (start and end):
        return []
    needle = normalize_ro(params.label_contains).casefold()
    findings = []
    for document, page, facts in context.page_facts():
        for fact in facts.dates:
            when = parse_ro_date(fact.value)
            if needle in normalize_ro(fact.label).casefold() and when and not start <= when <= end:
                findings.append(
                    finding(
                        rule,
                        "date_outside_period",
                        Evidence(document.id, page.number, fact.quote, locate=fact.value),
                        label=fact.label,
                        date=fact.value,
                        document=document.filename,
                        start=context.form["start_date"],
                        end=context.form["end_date"],
                    )
                )
    return findings
