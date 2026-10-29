import json
import re
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import FakeProvider, MakeClient, as_user, prompt_of, run_sql
from tests.flows import (
    add_regulation,
    add_rule,
    create_project,
    create_project_type,
    upload,
    verify,
)
from tests.pdf_factory import make_pdf

GUIDE = [
    "Art. 4 Cererea se depune impreuna cu certificatul constatator emis de ONRC.",
    "Art. 5 Se anexeaza si declaratia pe propria raspundere a reprezentantului legal.",
]
CERTIFICATE = {
    "name": "Certificat constatator",
    "description": "Emis de ONRC.",
    "regulation_quote": "certificatul constatator emis de ONRC",
}
DECLARATION = {
    "name": "Declaratie pe propria raspundere",
    "description": "",
    "regulation_quote": "declaratia pe propria raspundere a reprezentantului legal",
}


APPLIES = {"applies_because": "The applicant provides it.", "applies": True}


def reading(*documents: dict[str, Any], extra: list[dict[str, Any]] | None = None) -> FakeProvider:
    """A provider that lists `documents`, each citing the first regulation passage it was given,
    plus the `extra` items as they are (a model's mistakes)."""

    def answer(body: dict[str, Any]) -> str:
        label = re.search(r"\[(P\d+)\]", prompt_of(body))
        assert label, "the regulation passages reach the model"
        grounded = [APPLIES | {"source": label.group(1)} | document for document in documents]
        return json.dumps({"documents": grounded + [APPLIES | item for item in extra or []]})

    return FakeProvider(answers={"DocumentList": answer})


def listed(client: TestClient, project_id: int, user: str = "client") -> list[dict[str, Any]]:
    as_user(client, user)
    response = client.get(f"/api/projects/{project_id}/required-documents")
    assert response.status_code == 200, response.text
    items: list[dict[str, Any]] = response.json()
    return items


def test_a_new_project_gets_the_documents_its_regulations_require(make_client: MakeClient) -> None:
    mistakes = [
        {"source": "P99999", "name": "Ghost", "description": "", "regulation_quote": "x"},
        {"source": "W-NONE", "name": "Unknown rule", "description": "", "regulation_quote": ""},
    ]
    invented = {"name": "Invented", "description": "", "regulation_quote": "words nobody wrote"}
    twice = CERTIFICATE | {"description": "Twice"}
    not_asked = DECLARATION | {"applies": False}
    provider = reading(CERTIFICATE, twice, invented, not_asked, extra=mistakes)
    client = make_client(provider)
    type_id = create_project_type(client)
    add_regulation(client, "client", "guide.pdf", GUIDE, project_type_id=type_id)
    add_regulation(client, "reviewer", "audit.pdf", ["Art. 9 Raportul de audit intern."])

    project_id = create_project(client, type_id)

    [item] = listed(client, project_id)
    assert (item["name"], item["description"], item["source"]) == (
        "Certificat constatator",
        "Emis de ONRC.",
        "regulations",
    )
    assert (item["regulation_filename"], item["regulation_page"]) == ("guide.pdf", 1)
    assert item["regulation_quote"] == CERTIFICATE["regulation_quote"]
    [asked] = provider.schema_requests("DocumentList")
    assert "certificatul constatator" in prompt_of(asked)
    assert "Infrastructure" in prompt_of(asked), "the model is told the kind of project"
    assert "audit intern" not in prompt_of(asked), "reviewer regulations stay out"


def test_written_rules_count_and_no_regulation_means_no_model_call(
    make_client: MakeClient,
) -> None:
    tax = APPLIES | {
        "source": "W-TAX",
        "name": "Tax certificate",
        "description": "",
        "regulation_quote": "",
    }
    provider = FakeProvider(answers={"DocumentList": json.dumps({"documents": [tax]})})
    client = make_client(provider)
    type_id = create_project_type(client)

    bare = create_project(client, type_id)
    assert listed(client, bare) == []
    assert provider.schema_requests("DocumentList") == []

    add_rule(client, "client", code="W-TAX", title="Tax", description="Attach a tax certificate.")
    with_rule = create_project(client, type_id)

    [item] = listed(client, with_rule)
    assert (item["name"], item["regulation_filename"], item["regulation_quote"]) == (
        "Tax certificate",
        None,
        None,
    )


def test_admin_edits_stay_when_the_regulations_are_read_again(make_client: MakeClient) -> None:
    client = make_client(reading(CERTIFICATE, DECLARATION))
    type_id = create_project_type(client)
    add_regulation(client, "client", "guide.pdf", GUIDE, project_type_id=type_id)
    project_id = create_project(client, type_id)
    certificate, declaration = listed(client, project_id)

    as_user(client, "admin")
    added = client.post(
        f"/api/projects/{project_id}/required-documents",
        json={"name": "  Bilant  ", "description": "Last year"},
    ).json()
    edited = client.patch(
        f"/api/required-documents/{certificate['id']}", json={"description": "Max 30 days old"}
    ).json()
    assert client.delete(f"/api/required-documents/{declaration['id']}").status_code == 204
    again = client.post(f"/api/projects/{project_id}/required-documents/from-regulations")

    assert (added["name"], added["source"]) == ("Bilant", "admin")
    assert (edited["description"], edited["source"]) == ("Max 30 days old", "admin")
    assert edited["regulation_filename"] == "guide.pdf", "the edit keeps where it was read"
    assert [(i["name"], i["source"]) for i in again.json()] == [
        ("Certificat constatator", "admin"),
        ("Bilant", "admin"),
        ("Declaratie pe propria raspundere", "regulations"),
    ]
    assert again.json()[0]["description"] == "Max 30 days old"


def test_only_admins_change_the_list_and_only_the_owner_reads_it(make_client: MakeClient) -> None:
    client = make_client()
    project_id = create_project(client, create_project_type(client))
    list_url = f"/api/projects/{project_id}/required-documents"
    as_user(client, "admin")
    item = client.post(list_url, json={"name": "A"}).json()
    assert client.post(list_url, json={"name": " "}).status_code == 422
    assert (
        client.post("/api/projects/999/required-documents", json={"name": "A"}).status_code == 404
    )

    for user in ("client", "reviewer"):
        as_user(client, user)
        assert client.post(list_url, json={"name": "B"}).status_code == 403
        assert client.patch(f"/api/required-documents/{item['id']}", json={}).status_code == 403
        assert client.delete(f"/api/required-documents/{item['id']}").status_code == 403
        assert client.post(f"{list_url}/from-regulations").status_code == 403

    assert [i["name"] for i in listed(client, project_id, "client")] == ["A"]
    assert [i["name"] for i in listed(client, project_id, "admin")] == ["A"]
    for user in ("client-2", "reviewer"):  # not theirs; reviewers read submitted projects only
        as_user(client, user)
        assert client.get(list_url).status_code == 404
    upload(client, project_id, "a.pdf", ["A"])
    client.post(f"/api/projects/{project_id}/submit")
    assert [i["name"] for i in listed(client, project_id, "reviewer")] == ["A"]


def test_an_upload_can_be_added_for_an_item_of_the_list(make_client: MakeClient) -> None:
    client = make_client()
    type_id = create_project_type(client)
    project_id, other_id = create_project(client, type_id), create_project(client, type_id)
    as_user(client, "admin")
    item = client.post(f"/api/projects/{project_id}/required-documents", json={"name": "A"}).json()
    foreign = client.post(f"/api/projects/{other_id}/required-documents", json={"name": "B"}).json()

    as_user(client, "client")
    url = f"/api/projects/{project_id}/documents"
    pdf = {"file": ("a.pdf", make_pdf(["A"]), "application/pdf")}
    for wrong in (foreign["id"], 999):
        assert (
            client.post(url, params={"required_document_id": wrong}, files=pdf).status_code == 404
        )
    for_item = client.post(url, params={"required_document_id": item["id"]}, files=pdf).json()
    loose = upload(client, project_id, "b.pdf", ["B"])

    documents = client.get(f"/api/projects/{project_id}").json()["documents"]
    assert [(d["id"], d["required_document_id"]) for d in documents] == [
        (for_item["id"], item["id"]),
        (loose, None),
    ]
    as_user(client, "admin")
    client.delete(f"/api/required-documents/{item['id']}")
    rows = run_sql("SELECT count(*) AS n FROM project_documents WHERE required_document_id IS NULL")
    assert rows[0].n == 2, "deleting an item keeps the documents uploaded for it"


def test_without_a_provider_the_list_stays_empty_and_an_admin_is_told(
    make_client: MakeClient,
) -> None:
    client = make_client(ai_api_key=None, ai_fallback_api_key=None)
    type_id = create_project_type(client)
    add_regulation(client, "client", "guide.pdf", GUIDE, project_type_id=type_id)

    project_id = create_project(client, type_id)

    assert listed(client, project_id) == []
    as_user(client, "admin")
    again = client.post(f"/api/projects/{project_id}/required-documents/from-regulations")
    assert again.status_code == 503
    assert "AI_PROVIDER" in again.json()["detail"]


def test_an_uploaded_document_can_be_linked_to_an_item_later(make_client: MakeClient) -> None:
    client = make_client()
    type_id = create_project_type(client)
    project_id, other_id = create_project(client, type_id), create_project(client, type_id)
    as_user(client, "admin")
    item = client.post(f"/api/projects/{project_id}/required-documents", json={"name": "A"}).json()
    foreign = client.post(f"/api/projects/{other_id}/required-documents", json={"name": "B"}).json()
    document_id = upload(client, project_id, "a.pdf", ["A"])  # outside the list
    url = f"/api/projects/{project_id}/documents/{document_id}"

    as_user(client, "client")
    linked = client.patch(url, json={"required_document_id": item["id"]})
    for wrong in (foreign["id"], 999):
        assert client.patch(url, json={"required_document_id": wrong}).status_code == 404
    assert (
        client.get(f"/api/projects/{project_id}").json()["documents"][0]["required_document_id"]
        == item["id"]
    ), "a refused link changes nothing"
    unlinked = client.patch(url, json={"required_document_id": None})

    assert linked.json()["required_document_id"] == item["id"]
    assert unlinked.json()["required_document_id"] is None
    for user, refused in (("client-2", 404), ("reviewer", 403)):
        as_user(client, user)  # not the owner; reviewers never change a file
        assert client.patch(url, json={"required_document_id": None}).status_code == refused
    as_user(client, "client")
    client.post(f"/api/projects/{project_id}/submit")
    assert client.patch(url, json={"required_document_id": item["id"]}).status_code == 409


NO_FACTS = json.dumps(
    {"document_type": None, "parties": [], "ibans": [], "amounts": [], "dates": []}
)
MISSING = "completeness.required_document_missing"


def two_item_project(client: TestClient) -> tuple[int, list[dict[str, Any]]]:
    """A project whose list asks for a "Cerere" and an "Extras de cont", nothing uploaded."""
    project_id = create_project(client, create_project_type(client))
    as_user(client, "admin")
    url = f"/api/projects/{project_id}/required-documents"
    return project_id, [
        client.post(url, json={"name": name}).json() for name in ("Cerere", "Extras de cont")
    ]


def upload_for(client: TestClient, project_id: int, item: dict[str, Any], name: str) -> None:
    as_user(client, "client")
    response = client.post(
        f"/api/projects/{project_id}/documents",
        params={"required_document_id": item["id"]},
        files={"file": (name, make_pdf([name]), "application/pdf")},
    )
    assert response.status_code == 201, response.text


def test_a_file_missing_a_required_document_gets_only_that_error(make_client: MakeClient) -> None:
    provider = FakeProvider(answers={"PageFacts": NO_FACTS})
    client = make_client(provider)
    project_id, (cerere, extras) = two_item_project(client)
    upload_for(client, project_id, cerere, "cerere.pdf")

    [finding] = verify(client, project_id)["findings"]

    assert finding["rule_code"] == MISSING
    assert "Extras de cont" in finding["reason"]["en"]
    assert "Extras de cont" in finding["reason"]["ro"]
    assert (finding["document_id"], finding["confidence"], finding["severity"]) == (
        None,
        1.0,
        "bad",
    )
    assert [body for body in provider.bodies if "messages" in body] == [], "nothing was read"

    upload_for(client, project_id, extras, "extras.pdf")
    complete = verify(client, project_id)

    assert complete["findings"] == []
    assert len(provider.schema_requests("PageFacts")) == 2, "now both documents are checked"


def test_a_document_uploaded_outside_the_list_does_not_complete_it(make_client: MakeClient) -> None:
    client = make_client(FakeProvider(answers={"PageFacts": NO_FACTS}))
    project_id, (cerere, extras) = two_item_project(client)
    upload_for(client, project_id, cerere, "cerere.pdf")
    upload(client, project_id, "extras.pdf", ["Extras"])  # no item given

    assert [f["rule_code"] for f in verify(client, project_id)["findings"]] == [MISSING]
    unlinked = client.get(f"/api/projects/{project_id}").json()["documents"][1]["id"]
    client.patch(
        f"/api/projects/{project_id}/documents/{unlinked}",
        json={"required_document_id": extras["id"]},
    )
    assert verify(client, project_id)["findings"] == []


def test_the_reviewer_gets_the_same_error_on_an_incomplete_submission(
    make_client: MakeClient,
) -> None:
    provider = FakeProvider(answers={"PageFacts": NO_FACTS})
    client = make_client(provider)
    project_id, (cerere, _) = two_item_project(client)
    upload_for(client, project_id, cerere, "cerere.pdf")
    client.post(f"/api/projects/{project_id}/submit")

    as_user(client, "reviewer")
    [finding] = verify(client, project_id)["findings"]

    assert finding["rule_code"] == MISSING
    assert [body for body in provider.bodies if "messages" in body] == []
