from app.romanian import is_valid_cui, is_valid_iban
from app.verification.checks.common import finding
from app.verification.checks.registry import NoParams, register_check
from app.verification.context import RuleView, VerificationContext
from app.verification.findings import Evidence, FindingDraft


@register_check(
    "identifiers.cui_valid",
    {
        "en": "Every CUI/CIF on the documents has a valid check digit.",
        "ro": "Fiecare CUI/CIF din documente are cifra de control corectă.",
    },
    NoParams,
)
def cui_valid(context: VerificationContext, rule: RuleView, _: NoParams) -> list[FindingDraft]:
    return [
        finding(
            rule,
            "cui_invalid",
            Evidence(document.id, page.number, party.quote, locate=party.cui),
            cui=party.cui,
            party=party.name,
        )
        for document, page, facts in context.page_facts()
        for party in facts.parties
        if party.cui and not is_valid_cui(party.cui)
    ]


@register_check(
    "identifiers.iban_valid",
    {
        "en": "Every IBAN on the documents passes the mod-97 check.",
        "ro": "Fiecare IBAN din documente trece verificarea mod-97.",
    },
    NoParams,
)
def iban_valid(context: VerificationContext, rule: RuleView, _: NoParams) -> list[FindingDraft]:
    return [
        finding(
            rule,
            "iban_invalid",
            Evidence(document.id, page.number, iban.quote, locate=iban.value),
            iban=iban.value,
        )
        for document, page, facts in context.page_facts()
        for iban in facts.ibans
        if not is_valid_iban(iban.value)
    ]
