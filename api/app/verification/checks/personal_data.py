"""CNPs compared by keyed hash only: the check never sees, logs or stores a CNP in clear."""

from collections import Counter

from app.localized import LocalizedText
from app.verification.checks.common import finding
from app.verification.checks.registry import NoParams, register_check
from app.verification.context import IdentifierView, RuleView, VerificationContext
from app.verification.findings import Evidence, FindingDraft


def _evidence(context: VerificationContext, identifier: IdentifierView) -> Evidence | None:
    if identifier.document_id is None or identifier.page is None:
        return None
    document = context.document(identifier.document_id)
    page = document.page(identifier.page) if document else None
    if page is None or identifier.start is None or identifier.end is None:
        return None
    # Shown masked; located on the page by its text, which the document already contains.
    return Evidence(
        identifier.document_id,
        identifier.page,
        f"CNP {identifier.masked}",
        locate=page.text[identifier.start : identifier.end],
    )


def _where(context: VerificationContext, identifier: IdentifierView) -> LocalizedText:
    document = context.document(identifier.document_id or 0)
    if document is None:
        return {"en": "the application form", "ro": "cerere"}
    return {
        "en": f"{document.filename}, page {identifier.page}",
        "ro": f"{document.filename}, pagina {identifier.page}",
    }


@register_check(
    "personal_data.cnp_valid",
    {
        "en": "Every CNP has a valid check digit.",
        "ro": "Fiecare CNP are cifra de control corectă.",
    },
    NoParams,
)
def cnp_valid(context: VerificationContext, rule: RuleView, _: NoParams) -> list[FindingDraft]:
    return [
        finding(
            rule,
            "cnp_invalid",
            _evidence(context, identifier),
            masked=identifier.masked,
            where=_where(context, identifier),
        )
        for identifier in context.identifiers
        if identifier.kind == "cnp" and not identifier.valid
    ]


@register_check(
    "personal_data.cnp_consistent",
    {
        "en": "Every valid CNP in the documents is the legal representative's CNP from the form"
        " (or, without one in the form, the same CNP throughout).",
        "ro": "Fiecare CNP valid din documente este CNP-ul reprezentantului legal din cerere"
        " (sau, dacă cererea nu are unul, același CNP peste tot).",
    },
    NoParams,
)
def cnp_consistent(context: VerificationContext, rule: RuleView, _: NoParams) -> list[FindingDraft]:
    cnps = [i for i in context.identifiers if i.kind == "cnp" and i.valid]
    declared = [i.value_hash for i in cnps if i.document_id is None]
    in_documents = [i for i in cnps if i.document_id is not None]
    if declared:
        expected, key = declared[0], "cnp_differs_from_form"
    elif in_documents:
        expected = Counter(i.value_hash for i in in_documents).most_common(1)[0][0]
        key = "cnp_differs_between_documents"
    else:
        return []
    return [
        finding(
            rule,
            key,
            _evidence(context, identifier),
            masked=identifier.masked,
            where=_where(context, identifier),
        )
        for identifier in in_documents
        if identifier.value_hash != expected
    ]
