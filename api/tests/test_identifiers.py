"""The CUI check applies the ANAF formula to the number on the page, not to its label."""

from typing import cast

from app.personal_data import IdentifierHasher
from app.regulations.search import PassageSearch
from app.verification.checks.identifiers import cui_valid
from app.verification.checks.registry import NoParams
from app.verification.context import DocumentView, PageView, RuleView, VerificationContext
from app.verification.facts import ExtractedParty, PageFacts
from app.vocabulary import Scope, Severity


def party(name: str, cui: str) -> ExtractedParty:
    return ExtractedParty(name=name, cui=cui, role=None, quote=f"{name}, {cui}")


def test_only_a_wrong_check_digit_is_reported() -> None:
    facts = PageFacts(
        document_type=None,
        parties=[
            party("Zenit Pharma Distrib SRL", "CUI 412764070"),
            party("Banca Test S.A.", "CUI RO00000000"),
            party("Ion Pop", "1 9 0 0 1 0 1 1 2 3 4 5 6"),  # a CNP the model put in the CUI field
            party("Bad SRL", "CUI 361821"),
        ],
        ibans=[],
        amounts=[],
        dates=[],
    )
    page = PageView(0, 1, "text", [], False, None, facts, "v")
    context = VerificationContext(
        project_id=1,
        project_title="t",
        form={},
        scope=Scope.REVIEWER,
        documents=[DocumentView(1, "extras.pdf", None, [page])],
        identifiers=[],
        rules=[],
        passages=cast(PassageSearch, None),
        hasher=cast(IdentifierHasher, None),
    )
    rule = RuleView("identifiers.cui_valid", "CUI", "", Severity.BAD)
    found = cui_valid(context, rule, NoParams())
    assert [draft.evidence.locate for draft in found if draft.evidence] == ["CUI 361821"]
