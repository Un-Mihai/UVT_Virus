"""The application form against the documents: same applicant, same CUI, amounts that fit."""

from pydantic import BaseModel

from app.romanian import parse_ro_amount
from app.verification.checks.common import company_key, cui_digits, finding
from app.verification.checks.registry import NoParams, register_check
from app.verification.context import RuleView, VerificationContext
from app.verification.findings import Evidence, FindingDraft


@register_check(
    "form.applicant_cui_matches_documents",
    {
        "en": "Wherever the documents name the applicant, they give the CUI from the form.",
        "ro": "Oriunde documentele numesc solicitantul, ele indică CUI-ul din cerere.",
    },
    NoParams,
)
def applicant_cui_matches(
    context: VerificationContext, rule: RuleView, _: NoParams
) -> list[FindingDraft]:
    form_cui = cui_digits(context.form.get("applicant_cui") or "")
    applicant = company_key(context.form.get("applicant_name") or "")
    if not (form_cui and applicant):
        return []
    return [
        finding(
            rule,
            "applicant_cui_mismatch",
            Evidence(document.id, page.number, party.quote, locate=party.cui),
            document=document.filename,
            party=party.name,
            cui=party.cui,
            form_cui=context.form["applicant_cui"],
        )
        for document, page, facts in context.page_facts()
        for party in facts.parties
        if party.cui and company_key(party.name) == applicant and cui_digits(party.cui) != form_cui
    ]


class AmountWithinTotalParams(BaseModel):
    # Which document carries the total the requested amount must not exceed.
    document_type: str = "budget"


@register_check(
    "form.requested_amount_within_total",
    {
        "en": "The amount requested in the form is at most the grand total of the given document"
        " type.",
        "ro": "Suma solicitată în cerere este cel mult totalul general al tipului de document"
        " indicat.",
    },
    AmountWithinTotalParams,
)
def requested_amount_within_total(
    context: VerificationContext, rule: RuleView, params: AmountWithinTotalParams
) -> list[FindingDraft]:
    requested = parse_ro_amount(context.form.get("requested_amount") or "")
    if requested is None:
        return []
    findings = []
    for document, page, facts in context.page_facts():
        if document.document_type != params.document_type:
            continue
        for amount in facts.amounts:
            total = parse_ro_amount(amount.value)
            if amount.kind == "grand_total" and total is not None and requested > total:
                findings.append(
                    finding(
                        rule,
                        "requested_amount_above_total",
                        Evidence(document.id, page.number, amount.quote, locate=amount.value),
                        requested=requested,
                        total=total,
                        document=document.filename,
                    )
                )
    return findings
