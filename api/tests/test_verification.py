import json
import re
from typing import Any

from fastapi.testclient import TestClient

from app.personal_data import MaskedText
from app.verification.agents.extraction import _verified
from app.verification.facts import PageFacts
from tests.conftest import FakeProvider, MakeClient, as_user, prompt_of
from tests.flows import (
    FORM,
    add_regulation,
    add_rule,
    create_project,
    create_project_type,
    upload,
    verify,
)
from tests.test_pdf import annotations_of
from tests.test_romanian import make_cnp

# Synthetic data only: fake company, valid-looking but invented CNPs.
CNP_A = make_cnp("190010112345")
CNP_B = make_cnp("280020212345")
CONTRACT = [
    "CONTRACT DE FINANTARE nr. 12/2026",
    "Beneficiar: Alfa Construct SRL, CUI RO 361821",
    f"Reprezentant legal: Ion Pop, CNP {CNP_A}",
    "Garantia de buna executie este 5% din valoare.",
]
BUDGET = [
    "BUGET PROIECT",
    "Lucrari: 1.000,00 lei",
    "Echipamente: 500,00 lei",
    "Subtotal: 1.600,00 lei",
    f"Intocmit de Ion Pop, CNP {CNP_B}",
]
GUARANTEE_QUOTE = "Garantia de buna executie este 5% din valoare."


def amount(label: str, value: str, kind: str, quote: str) -> dict[str, Any]:
    return {"label": label, "value": value, "currency": "RON", "kind": kind, "quote": quote}


def page_facts(body: dict[str, Any]) -> str:
    page = prompt_of(body)
    if "CONTRACT" in page:
        facts = {
            "document_type": "contract",
            "parties": [
                {
                    "name": "Alfa Construct SRL",
                    "cui": "RO 361821",
                    "role": "beneficiary",
                    "quote": "Beneficiar: Alfa Construct SRL, CUI RO 361821",
                }
            ],
            "ibans": [],
            # Not on the page: must be dropped, never shown as evidence.
            "amounts": [
                amount("Valoare totala", "999.999,00", "grand_total", "Valoare 999.999,00")
            ],
            "dates": [],
        }
    else:
        facts = {
            "document_type": "budget",
            "parties": [],
            "ibans": [],
            "amounts": [
                amount("Lucrari", "1.000,00", "line_total", "Lucrari: 1.000,00 lei"),
                amount("Echipamente", "500,00", "line_total", "Echipamente: 500,00 lei"),
                amount("Subtotal", "1.600,00", "subtotal", "Subtotal: 1.600,00 lei"),
            ],
            "dates": [],
        }
    return json.dumps(facts)


REGULATIONS = {
    "cui": "Art. 1 The CUI of the beneficiary must be valid.",
    "guarantee": "Art. 2 The performance guarantee is at least 10% of the contract value.",
    "sums": "Art. 7 The budget subtotal equals the sum of its lines.",
    "call": "Call 12: every application includes a guarantee letter.",
    "other": "SECRET RULE OF ANOTHER PROJECT",
    "audit": "Audit 3: the performance guarantee is at least 10% of the contract.",
}


def label(prompt: str, key: str) -> str | None:
    """The id the prompt gives the passage holding REGULATIONS[key], when it was retrieved."""
    match = re.search(r"\[(P\d+)\] [^\n]+\n" + re.escape(REGULATIONS[key]), prompt)
    return match.group(1) if match else None


def reason(text: str) -> dict[str, str]:
    return {
        "reason_en": text,
        "reason_ro": f"(ro) {text}",
        "recommendation_en": "Fix it.",
        "recommendation_ro": "Corectați.",
    }


def document_review(body: dict[str, Any]) -> str:
    prompt = prompt_of(body)
    document = re.search(r"DOCUMENT (\d+): (\S+)", prompt)
    assert document, "the prompt names the document"
    discrepancies: list[dict[str, Any]] = []
    checks: list[dict[str, str]] = []
    if document.group(2) == "contract.pdf":
        guarantee = label(prompt, "guarantee") or label(prompt, "audit")
        assert guarantee, "a guarantee requirement was retrieved"
        found = {"page": 1, "source": guarantee, "severity": "warn"} | reason("Guarantee low.")
        discrepancies = [
            found
            | {
                "quote": GUARANTEE_QUOTE,
                "regulation_quote": "An invented regulation requirement",
                "confidence": 1,
            },
            found
            | {
                "quote": GUARANTEE_QUOTE,
                "regulation_quote": "the performance guarantee is at least 10%",
                "confidence": 0.7,
            },
            # Neither of these may become a finding: invented quote, unknown source.
            found | {"quote": "Garantia este de 20%", "regulation_quote": "", "confidence": 0.95},
            found
            | {
                "quote": GUARANTEE_QUOTE,
                "source": "P999999",
                "regulation_quote": "",
                "confidence": 1,
            },
        ]
        if cui := label(prompt, "cui"):
            checks.append({"check_id": "identifiers.cui_valid", "params": "{}", "source": cui})
        checks.append({"check_id": "nope", "params": "{}", "source": guarantee})
    elif sums := label(prompt, "sums"):
        checks.append({"check_id": "amounts.totals_add_up", "params": "{}", "source": sums})
        if cui := label(prompt, "cui"):  # asked twice in a run: runs once
            checks.append({"check_id": "identifiers.cui_valid", "params": "{}", "source": cui})
    return json.dumps({"discrepancies": discrepancies, "checks": checks})


def application_review(body: dict[str, Any]) -> str:
    prompt = prompt_of(body)
    issues = []
    if call := label(prompt, "call"):
        issues.append(
            {
                "source": call,
                "regulation_quote": "every application includes a guarantee letter",
                "severity": "bad",
                "confidence": 0.9,
            }
            | reason("No guarantee letter.")
        )
    if "[W-SIGN]" in prompt:
        issues.append(
            {"source": "W-SIGN", "regulation_quote": "", "severity": "bad", "confidence": 0.9}
            | reason("Contract not signed.")
        )
    return json.dumps({"issues": issues, "checks": []})


def set_up(client: TestClient) -> tuple[int, int, int]:
    type_id = create_project_type(client)
    project_id = create_project(client, type_id, FORM | {"legal_representative_cnp": CNP_A})
    other_project = create_project(client, type_id)
    add_regulation(
        client, "client", "everyone.pdf", [REGULATIONS["cui"]], [REGULATIONS["guarantee"]]
    )
    add_regulation(client, "client", "type.pdf", [REGULATIONS["sums"]], project_type_id=type_id)
    add_regulation(client, "client", "call.pdf", [REGULATIONS["call"]], project_id=project_id)
    add_regulation(client, "client", "other.pdf", [REGULATIONS["other"]], project_id=other_project)
    add_regulation(client, "reviewer", "audit.pdf", [REGULATIONS["audit"]])
    signed = "The contract is signed by both parties."
    add_rule(client, "client", code="W-SIGN", title="Signed contract", description=signed)
    contract_id = upload(client, project_id, "contract.pdf", CONTRACT)
    upload(client, project_id, "budget.pdf", BUDGET)
    return project_id, contract_id, type_id


def test_documents_are_checked_against_the_regulations_that_apply(make_client: MakeClient) -> None:
    provider = FakeProvider(
        answers={
            "PageFacts": page_facts,
            "DocumentReview": document_review,
            "ApplicationReview": application_review,
        }
    )
    client = make_client(provider)
    project_id, contract_id, _ = set_up(client)

    as_user(client, "client")
    client_report = verify(client, project_id)

    by_rule = {finding["rule_code"]: finding for finding in client_report["findings"]}
    # The 0.7 discrepancy is under the client's 0.85 threshold; the invented quote and the
    # unknown source are dropped; the CUI check asked for twice ran once.
    assert sorted(by_rule) == [
        "W-SIGN",
        "amounts.totals_add_up",
        "call.pdf p.1",
        "identifiers.cui_valid",
    ]
    assert len(client_report["findings"]) == 4
    cui = by_rule["identifiers.cui_valid"]
    assert (cui["agent"], cui["confidence"], cui["document_name"]) == (
        "checks",
        1.0,
        "contract.pdf",
    )
    assert cui["regulation"] | {"document_id": 0} == {
        "document_id": 0,
        "filename": "everyone.pdf",
        "page": 1,
        "quote": None,
    }
    assert cui["rects"], "the CUI is highlighted on the page"
    assert by_rule["amounts.totals_add_up"]["regulation"]["filename"] == "type.pdf"
    cited = f"/api/projects/{project_id}/regulations/{cui['regulation']['document_id']}/file"
    assert client.get(cited).content.startswith(b"%PDF-")
    call = by_rule["call.pdf p.1"]
    assert (call["document_id"], call["regulation"]["filename"]) == (None, "call.pdf")
    assert call["regulation"]["quote"] == "every application includes a guarantee letter"
    assert by_rule["W-SIGN"]["regulation"] is None
    assert by_rule["W-SIGN"]["reason"] == {
        "en": "Contract not signed.",
        "ro": "(ro) Contract not signed.",
    }

    # What the model was asked (embedding requests also carry regulation text, at indexing).
    client_prompts = json.dumps([body for body in provider.bodies if "messages" in body])
    for key in ("cui", "sums", "call"):
        assert REGULATIONS[key] in client_prompts, key
    assert REGULATIONS["other"] not in client_prompts, "another project's regulation stays out"
    assert REGULATIONS["audit"] not in client_prompts, "reviewer regulations stay out"
    assert CNP_A not in client_prompts
    assert CNP_B not in client_prompts

    highlights = client.get(f"/api/projects/{project_id}/documents/{contract_id}/highlights").json()
    assert highlights["pages"] == [{"number": 1, "width": 595.0, "height": 842.0, "is_scan": False}]
    assert [finding["anchor"] for finding in highlights["findings"]] == [f"finding-{cui['id']}"]
    annotated = client.get(f"/api/projects/{project_id}/documents/{contract_id}/annotated")
    assert [str(a["/NM"]) for a in annotations_of(annotated.content)] == [f"finding-{cui['id']}"]

    client.post(f"/api/projects/{project_id}/submit")
    as_user(client, "reviewer")
    seen = len(provider.bodies)
    reviewer_report = verify(client, project_id)

    [finding] = reviewer_report["findings"]
    assert (finding["rule_code"], finding["confidence"]) == ("audit.pdf p.1", 0.7)
    assert finding["quote"] == GUARANTEE_QUOTE
    assert finding["regulation"]["quote"] == "the performance guarantee is at least 10%"
    # A client-scope regulation does not open for a reviewer.
    assert client.get(cited).status_code == 404
    reviewer_prompts = json.dumps([body for body in provider.bodies[seen:] if "messages" in body])
    assert REGULATIONS["cui"] not in reviewer_prompts, "client regulations stay out"
    assert "W-SIGN" not in reviewer_prompts
    # Pages were read once; the reviewer run reused the cached facts.
    assert len(provider.schema_requests("PageFacts")) == 2

    confirmed = client.post(
        f"/api/findings/{finding['id']}/decision",
        json={"decision": "confirmed", "note": "Checked the contract."},
    )
    assert confirmed.json()["decision"] == "confirmed"
    assert confirmed.json()["regulation"]["filename"] == "audit.pdf"
    as_user(client, "client")
    decide = client.post(f"/api/findings/{finding['id']}/decision", json={"decision": "dismissed"})
    assert decide.status_code == 404


def test_without_regulations_or_rules_there_is_nothing_to_judge_against(
    make_client: MakeClient,
) -> None:
    provider = FakeProvider(answers={"PageFacts": page_facts})
    client = make_client(provider)
    project_id = create_project(client, create_project_type(client))
    upload(client, project_id, "contract.pdf", CONTRACT)

    as_user(client, "client")
    report = verify(client, project_id)

    assert report["findings"] == []
    assert provider.schema_requests("DocumentReview") == []


def test_every_page_is_reviewed_even_when_the_document_exceeds_the_context(
    make_client: MakeClient,
) -> None:
    provider = FakeProvider(
        answers={
            "PageFacts": page_facts,
            "DocumentReview": '{"discrepancies": [], "checks": []}',
            "ApplicationReview": '{"issues": [], "checks": []}',
        }
    )
    client = make_client(provider, compliance_context_chars=2000)
    project_id = create_project(client, create_project_type(client))
    add_regulation(client, "client", "guide.pdf", [REGULATIONS["cui"]])
    upload(
        client,
        project_id,
        "long.pdf",
        [f"Synthetic application line {line}: details for review." for line in range(35)],
        ["LAST PAGE REQUIREMENT EVIDENCE"],
    )

    verify(client, project_id)

    prompts = [prompt_of(body) for body in provider.schema_requests("DocumentReview")]
    assert any("LAST PAGE REQUIREMENT EVIDENCE" in prompt for prompt in prompts)
    assert any("--- page 2 ---" in prompt for prompt in prompts)
    assert len(prompts) >= 3  # a long first page is split too


def test_changed_embedding_dimensions_use_the_text_fallback(make_client: MakeClient) -> None:
    provider = FakeProvider(
        answers={
            "PageFacts": page_facts,
            "DocumentReview": document_review,
            "ApplicationReview": application_review,
        }
    )
    original = make_client(provider)
    project_id, _, _ = set_up(original)
    changed = as_user(make_client(provider, ai_embedding_dimensions=16), "client")

    report = verify(changed, project_id)

    assert len(report["findings"]) == 4


def test_a_failed_run_is_recorded_with_its_reason(make_client: MakeClient) -> None:
    client = make_client(ai_api_key=None, ai_fallback_api_key=None)
    project_id, _, _ = set_up(client)

    as_user(client, "client")
    client.post(f"/api/projects/{project_id}/verifications")
    run = client.get(f"/api/projects/{project_id}/verifications/latest").json()["run"]

    assert run["status"] == "failed"
    assert "AINotConfiguredError" in run["error"]


def test_admins_do_not_run_verifications(make_client: MakeClient) -> None:
    client = make_client()
    project_id, _, _ = set_up(client)

    as_user(client, "admin")
    assert client.post(f"/api/projects/{project_id}/verifications").status_code == 403
    as_user(client, "client")
    assert client.get(f"/api/projects/{project_id}/verifications/latest").status_code == 404


def test_extracted_facts_need_their_quote_on_the_page() -> None:
    page = "Beneficiar: Alfa SRL, CUI RO 361820\nTotal general: 1.500,00 lei"
    facts = PageFacts.model_validate_json(
        json.dumps(
            {
                "document_type": "invoice",
                "parties": [
                    {
                        "name": "Alfa SRL",
                        "cui": "RO 361820",
                        "role": None,
                        "quote": "Alfa SRL, CUI RO 361820",
                    },
                    {
                        "name": "Beta SA",
                        "cui": "RO 999",
                        "role": None,
                        "quote": "Beta SA, CUI RO 999",
                    },
                ],
                "ibans": [],
                "amounts": [
                    amount("Total", "1.500,00", "grand_total", "Total general: 1.500,00 lei"),
                    amount("Total", "9.999,00", "grand_total", "Total general: 1.500,00 lei"),
                ],
                "dates": [],
            }
        )
    )

    kept = _verified(facts, MaskedText(page), page)

    assert [party.name for party in kept.parties] == ["Alfa SRL"]
    assert [item.value for item in kept.amounts] == ["1.500,00"]  # value must be in its quote
