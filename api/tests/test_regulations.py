from typing import Any

from tests.conftest import FakeProvider, MakeClient, as_user, run_sql
from tests.flows import add_regulation, add_rule, create_project, create_project_type
from tests.test_romanian import make_cnp

GUIDE = ["Art. 5 Garantia de buna executie este de minimum 10%.", "Art. 6 Termen: 30 de zile."]


def test_only_admins_manage_regulations(make_client: MakeClient) -> None:
    client = make_client()
    type_id = create_project_type(client)

    for user in ("client", "reviewer"):
        as_user(client, user)
        assert client.get("/api/regulations", params={"scope": "client"}).status_code == 403
        assert client.get("/api/checks").status_code == 403
        assert client.get("/api/admin/projects").status_code == 403
        assert client.post("/api/project-types", json={"code": "x", "name": "X"}).status_code == 403
        # Everyone signed in can read the project types, to apply for one.
        assert client.get("/api/project-types").json()[0]["id"] == type_id


def test_regulations_live_at_three_levels_and_two_scopes(make_client: MakeClient) -> None:
    client = make_client()
    type_id = create_project_type(client)
    project_id = create_project(client, type_id)
    add_regulation(client, "client", "everyone.pdf", GUIDE)
    add_regulation(client, "client", "type.pdf", GUIDE, project_type_id=type_id)
    add_regulation(client, "client", "project.pdf", GUIDE, project_id=project_id)
    add_regulation(client, "reviewer", "audit.pdf", GUIDE)

    def names(**level: str | int) -> list[str]:
        listed = client.get("/api/regulations", params=level).json()
        return [document["filename"] for document in listed["documents"]]

    assert names(scope="client") == ["everyone.pdf"]
    assert names(scope="client", project_type_id=type_id) == ["type.pdf"]
    assert names(scope="client", project_id=project_id) == ["project.pdf"]
    assert names(scope="reviewer") == ["audit.pdf"]
    both: dict[str, str | int] = {
        "scope": "client",
        "project_type_id": type_id,
        "project_id": project_id,
    }
    assert client.get("/api/regulations", params=both).status_code == 400
    missing: dict[str, str | int] = {"scope": "client", "project_id": 999}
    assert client.get("/api/regulations", params=missing).status_code == 404
    assert [p["id"] for p in client.get("/api/admin/projects").json()] == [project_id]


def test_uploads_are_split_into_embedded_passages(make_client: MakeClient) -> None:
    client = make_client()

    uploaded = add_regulation(client, "client", "guide.pdf", GUIDE, ["Anexa 1"])

    listed = client.get("/api/regulations", params={"scope": "client"}).json()["documents"][0]
    assert uploaded["index_status"] == "pending"
    assert (listed["index_status"], listed["index_error"]) == ("done", None)
    rows = run_sql(
        "SELECT page, embedding_model, embedding IS NOT NULL AS embedded "
        "FROM regulation_passages ORDER BY page"
    )
    assert [(row.page, row.embedding_model, row.embedded) for row in rows] == [
        (1, "embed-test", True),
        (2, "embed-test", True),
    ]
    assert client.get(f"/api/regulation-documents/{uploaded['id']}/file").content[:5] == b"%PDF-"


def test_without_embeddings_passages_are_kept_and_can_be_processed_again(
    make_client: MakeClient,
) -> None:
    client = make_client(ai_api_key=None, ai_fallback_api_key=None)

    uploaded = add_regulation(client, "client", "guide.pdf", GUIDE)

    listed = client.get("/api/regulations", params={"scope": "client"}).json()["documents"][0]
    assert listed["index_status"] == "failed"
    assert "AI_PROVIDER" in listed["index_error"]
    [row] = run_sql("SELECT count(*) AS n FROM regulation_passages WHERE embedding IS NULL")
    assert row.n == 1
    working = as_user(make_client(), "admin")
    again = working.post(f"/api/regulation-documents/{uploaded['id']}/process")
    assert again.status_code == 202
    listed = working.get("/api/regulations", params={"scope": "client"}).json()["documents"][0]
    assert listed["index_status"] == "done"


def test_regulation_identifiers_are_masked_before_embedding(make_client: MakeClient) -> None:
    provider = FakeProvider()
    client = make_client(provider)
    cnp = make_cnp("190010112345")

    add_regulation(client, "client", "guide.pdf", [f"Synthetic representative CNP {cnp}"])

    inputs = [text for body in provider.bodies for text in body.get("input", [])]
    assert inputs
    assert all(cnp not in text for text in inputs)
    [passage] = run_sql("SELECT text FROM regulation_passages")
    assert cnp not in passage.text
    assert "[CNP#" in passage.text


def test_written_rules_are_plain_words_for_every_project_or_a_type(
    make_client: MakeClient,
) -> None:
    client = make_client()
    type_id = create_project_type(client)
    rule: dict[str, Any] = {
        "code": "W-1",
        "title": "Signed",
        "description": "The contract is signed.",
    }
    created = add_rule(client, "client", **rule)
    add_rule(client, "client", project_type_id=type_id, **rule)  # same code, other level
    add_rule(client, "reviewer", **rule)  # same code, other scope

    duplicate = client.post("/api/regulations/rules", json={"scope": "client"} | rule)
    updated = client.patch(f"/api/rules/{created['id']}", json={"active": False}).json()
    everyone = client.get("/api/regulations", params={"scope": "client"}).json()["rules"]

    assert duplicate.status_code == 409
    assert updated["active"] is False
    assert [(r["code"], r["project_type_id"]) for r in everyone] == [("W-1", None)]
    assert client.delete(f"/api/rules/{created['id']}").status_code == 204
    checks = {check["id"]: check for check in client.get("/api/checks").json()}
    assert set(checks["identifiers.cui_valid"]["description"]) == {"en", "ro"}
