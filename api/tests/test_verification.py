import json
import re
from typing import Any

from fastapi.testclient import TestClient

from app.personal_data import MaskedText
from app.verification.agents.extraction import _verified
from app.verification.facts import PageFacts
from tests.conftest import FakeProvider, MakeClient, as_user, prompt_of
from tests.flows import FORM, add_rule, create_project, create_project_type, upload, verify
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


def compliance(body: dict[str, Any]) -> str:
    match = re.search(r"=== document_id (\d+): contract\.pdf", prompt_of(body))
    assert match, "the prompt names each document by id"
    violation = {
        "document_id": int(match.group(1)),
        "page": 1,
        "reason_en": "The guarantee is below the 10% the regulation requires.",
        "reason_ro": "Garanția este sub pragul de 10% cerut de regulament.",
        "recommendation_en": "Raise the performance guarantee to at least 10%.",
        "recommendation_ro": "Majorați garanția de bună execuție la cel puțin 10%.",
        "severity": "warn",
    }
    return json.dumps(
        {
            "violations": [
                violation | {"quote": GUARANTEE_QUOTE, "confidence": 0.7},
                violation | {"quote": "Garantia este de 20%", "confidence": 0.95},  # invented
            ]
        }
    )


def set_up(client: TestClient) -> tuple[int, int, int]:
    type_id = create_project_type(client)
    checks = {
        "C-CUI": ("identifiers.cui_valid", {}),
        "C-FORM": ("form.applicant_cui_matches_documents", {}),
        "C-SUM": ("amounts.totals_add_up", {}),
        "C-CNP": ("personal_data.cnp_consistent", {}),
        "C-DOCS": (
            "completeness.required_documents",
            {"document_types": ["contract", "budget", "guarantee"]},
        ),
    }
    for code, (check_id, params) in checks.items():
        add_rule(
            client,
            type_id,
            "client",
            code=code,
            title=code,
            kind="check",
            check_id=check_id,
            params=params,
        )
    guarantee_rule = {"title": "Guarantee", "description": "At least 10%.", "kind": "ai"}
    add_rule(client, type_id, "client", code="C-G", **guarantee_rule)
    add_rule(client, type_id, "reviewer", code="R-G", **guarantee_rule)

    project_id = create_project(client, type_id, FORM | {"legal_representative_cnp": CNP_A})
    contract_id = upload(client, project_id, "contract.pdf", CONTRACT)
    upload(client, project_id, "budget.pdf", BUDGET)
    return project_id, contract_id, type_id


def test_client_and_reviewer_processes_end_to_end(make_client: MakeClient) -> None:
    provider = FakeProvider(answers={"PageFacts": page_facts, "ComplianceVerdict": compliance})
    client = make_client(provider)
    project_id, contract_id, _ = set_up(client)

    as_user(client, "client")
    client_report = verify(client, project_id)

    by_rule = {finding["rule_code"]: finding for finding in client_report["findings"]}
    # The 0.7 AI finding is under the client's 0.85 threshold; the invented quote is dropped.
    assert sorted(by_rule) == ["C-CNP", "C-CUI", "C-DOCS", "C-FORM", "C-SUM"]
    assert client_report["min_confidence"] == 0.85
    assert by_rule["C-CUI"]["quote"] == "Beneficiar: Alfa Construct SRL, CUI RO 361821"
    assert by_rule["C-CUI"]["document_name"] == "contract.pdf"
    assert by_rule["C-CUI"]["rects"], "the CUI is highlighted on the page"
    assert "1,500.00" in by_rule["C-SUM"]["reason"]["en"]
    assert "1.500,00" in by_rule["C-SUM"]["reason"]["ro"]
    assert "guarantee" in by_rule["C-DOCS"]["reason"]["en"]
    assert "garanția" in by_rule["C-DOCS"]["reason"]["ro"]
    assert not any(finding["ocr"] for finding in by_rule.values())
    assert by_rule["C-DOCS"]["document_id"] is None
    assert by_rule["C-CNP"]["document_name"] == "budget.pdf"
    assert CNP_B not in by_rule["C-CNP"]["quote"]
    assert by_rule["C-CNP"]["rects"]
    # No model ever saw a CNP in clear.
    assert CNP_A not in json.dumps(provider.bodies)
    assert CNP_B not in json.dumps(provider.bodies)

    highlights = client.get(f"/api/projects/{project_id}/documents/{contract_id}/highlights").json()
    assert highlights["pages"] == [{"number": 1, "width": 595.0, "height": 842.0, "is_scan": False}]
    anchors = sorted(finding["anchor"] for finding in highlights["findings"])
    assert anchors == sorted(f"finding-{by_rule[code]['id']}" for code in ("C-CUI", "C-FORM"))
    annotated = client.get(f"/api/projects/{project_id}/documents/{contract_id}/annotated")
    annotations = annotations_of(annotated.content)
    assert sorted(str(annotation["/NM"]) for annotation in annotations) == anchors

    client.post(f"/api/projects/{project_id}/submit")
    as_user(client, "reviewer")
    reviewer_report = verify(client, project_id)

    assert [f["rule_code"] for f in reviewer_report["findings"]] == ["R-G"]
    reviewer_finding = reviewer_report["findings"][0]
    assert (reviewer_finding["confidence"], reviewer_finding["agent"]) == (0.7, "compliance")
    assert reviewer_finding["reason"]["ro"].startswith("Garanția")
    assert reviewer_finding["quote"] == GUARANTEE_QUOTE
    # Pages were read once; the reviewer run reused the cached facts.
    assert len(provider.schema_requests("PageFacts")) == 2

    confirmed = client.post(
        f"/api/findings/{reviewer_finding['id']}/decision",
        json={"decision": "confirmed", "note": "Checked the contract."},
    )
    assert confirmed.json()["decision"] == "confirmed"
    assert confirmed.json()["decided_by"] == "user-1"
    as_user(client, "client")
    assert (
        client.post(
            f"/api/findings/{reviewer_finding['id']}/decision", json={"decision": "dismissed"}
        ).status_code
        == 404
    )


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
