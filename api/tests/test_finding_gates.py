"""What keeps a model's finding out (permissions, paraphrases) and keeps a check from doubling."""

import asyncio
from typing import cast

from app.personal_data import IdentifierHasher
from app.regulations.search import Passage, PassageSearch
from app.verification.agents.compliance import Source, _obliges
from app.verification.agents.form_checks import FormChecksAgent
from app.verification.context import (
    DocumentView,
    IdentifierView,
    PageView,
    RuleView,
    VerificationContext,
)
from app.verification.findings import CERTAIN, Evidence, FindingDraft, RegulationRef
from app.verification.orchestrator import _unique_checks
from app.vocabulary import Scope, Severity

RULE = RuleView("file.pdf p.1", "file.pdf", "", Severity.BAD)


def passage(text: str) -> Source:
    return Source(RULE, Passage(1, 1, "file.pdf", 1, text))


def test_a_finding_needs_the_passages_own_words_and_an_obligation_in_them() -> None:
    form = passage("Rubrica COD DE IDENTIFICARE se completează astfel: a) cu codul unic")
    assert _obliges(form, "se completează astfel")
    assert _obliges(passage("Banca are obligația de a informa clientul."), "obligația de a informa")
    assert _obliges(passage("The guarantee must be at least 10%."), "must be at least 10%")
    # Data an institution collects is a permission: no word obliges.
    collected = passage("- date de identificare a persoanei fizice: numele și prenumele, CNP")
    assert not _obliges(collected, "date de identificare a persoanei fizice")
    # Words that are not in the passage prove nothing, however firm they sound.
    assert not _obliges(form, "Formularul trebuie să conțină codul")
    assert not _obliges(form, "")


def test_a_written_rule_is_the_admins_own_wording() -> None:
    assert _obliges(Source(RULE, None), "anything")


def draft(agent: str, quote: str, regulation: RegulationRef | None = None) -> FindingDraft:
    return FindingDraft(
        rule_code="personal_data.cnp_valid",
        agent=agent,
        severity=Severity.BAD,
        confidence=CERTAIN,
        reason={"en": "r", "ro": "r"},
        recommendation={"en": "x", "ro": "x"},
        evidence=Evidence(1, 1, quote),
        regulation=regulation,
    )


def test_a_check_that_ran_twice_is_one_finding_and_keeps_the_citation() -> None:
    cited = draft("checks", "CNP 1*********870", RegulationRef(5, 21, None))
    assert _unique_checks([draft("checks", "CNP 1*********870"), cited]) == [cited]
    assert _unique_checks([cited, draft("checks", "CNP 1*********870")]) == [cited]
    # Another quote is another finding, and a model's findings are never merged.
    other = draft("checks", "CNP 2*********111")
    assert len(_unique_checks([cited, other])) == 2
    twins = [draft("compliance", "same"), draft("compliance", "same")]
    assert _unique_checks(twins) == twins


def test_the_cnp_check_digit_is_checked_without_the_model_asking() -> None:
    text = "CNP 1850728239870 în adeverință"
    page = PageView(0, 1, text, [], False, None, None, None)
    context = VerificationContext(
        project_id=1,
        project_title="t",
        form={},
        scope=Scope.REVIEWER,
        documents=[DocumentView(1, "adeverinta.pdf", None, [page])],
        identifiers=[
            IdentifierView(1, 1, "cnp", "h1", "1*********870", False, 4, 17),
            IdentifierView(1, 1, "cnp", "h2", "2*********111", True, 0, 0),
        ],
        rules=[],
        passages=cast(PassageSearch, None),
        hasher=cast(IdentifierHasher, None),
    )
    (found,) = asyncio.run(FormChecksAgent().run(context))
    assert found.rule_code == "personal_data.cnp_valid"
    assert found.evidence is not None
    assert found.evidence.quote == "CNP 1*********870"
