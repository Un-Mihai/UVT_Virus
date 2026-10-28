from tests.conftest import MakeClient, as_user
from tests.flows import add_rule, create_project_type
from tests.pdf_factory import make_pdf


def test_only_admins_manage_project_types_and_regulations(make_client: MakeClient) -> None:
    client = make_client()
    type_id = create_project_type(client)

    for user in ("client", "reviewer"):
        as_user(client, user)
        assert client.post("/api/project-types", json={"code": "x", "name": "X"}).status_code == 403
        assert client.get(f"/api/project-types/{type_id}/regulations/client").status_code == 403
        assert client.get("/api/checks").status_code == 403
        # Everyone signed in can read the project types, to apply for one.
        assert client.get("/api/project-types").json()[0]["id"] == type_id


def test_client_and_reviewer_rule_sets_stay_apart(make_client: MakeClient) -> None:
    client = make_client()
    type_id = create_project_type(client)
    add_rule(
        client,
        type_id,
        "client",
        code="C1",
        title="CUI valid",
        kind="check",
        check_id="identifiers.cui_valid",
    )
    add_rule(client, type_id, "reviewer", code="C1", title="Audit clause", kind="ai")

    client_set = client.get(f"/api/project-types/{type_id}/regulations/client").json()
    reviewer_set = client.get(f"/api/project-types/{type_id}/regulations/reviewer").json()

    assert [(r["code"], r["kind"]) for r in client_set["rules"]] == [("C1", "check")]
    assert [(r["code"], r["kind"]) for r in reviewer_set["rules"]] == [("C1", "ai")]
    duplicate = client.post(
        f"/api/project-types/{type_id}/regulations/client/rules",
        json={"code": "C1", "title": "Again", "kind": "ai"},
    )
    assert duplicate.status_code == 409
    assert client.get(f"/api/project-types/{type_id}/regulations/other").status_code == 422


def test_check_rules_must_name_a_registered_check_with_valid_params(
    make_client: MakeClient,
) -> None:
    client = make_client()
    type_id = create_project_type(client)
    url = f"/api/project-types/{type_id}/regulations/client/rules"

    unknown = client.post(
        url, json={"code": "X", "title": "X", "kind": "check", "check_id": "nope"}
    )
    bad_params = client.post(
        url,
        json={
            "code": "X",
            "title": "X",
            "kind": "check",
            "check_id": "completeness.required_documents",
        },
    )
    rule = add_rule(
        client,
        type_id,
        "client",
        code="X",
        title="Docs",
        kind="check",
        check_id="completeness.required_documents",
        params={"document_types": ["contract"]},
    )
    bad_update = client.patch(f"/api/rules/{rule['id']}", json={"params": {"document_types": 3}})

    assert unknown.status_code == 422
    assert "GET /api/checks" in unknown.json()["detail"]
    assert bad_params.status_code == 422
    assert bad_update.status_code == 422
    checks = {check["id"] for check in client.get("/api/checks").json()}
    assert {
        "identifiers.cui_valid",
        "personal_data.cnp_consistent",
        "amounts.totals_add_up",
    } <= checks


def test_admin_uploads_and_removes_regulation_documents(make_client: MakeClient) -> None:
    client = make_client()
    type_id = create_project_type(client)
    pdf = make_pdf(["Art. 5 Garantia de buna executie este de minimum 10%."])

    uploaded = client.post(
        f"/api/project-types/{type_id}/regulations/reviewer/documents",
        files={"file": ("audit.pdf", pdf, "application/pdf")},
    ).json()
    reviewer_docs = client.get(f"/api/project-types/{type_id}/regulations/reviewer").json()[
        "documents"
    ]
    client_docs = client.get(f"/api/project-types/{type_id}/regulations/client").json()["documents"]

    assert [doc["filename"] for doc in reviewer_docs] == ["audit.pdf"]
    assert client_docs == []
    assert client.get(f"/api/regulation-documents/{uploaded['id']}/file").content == pdf
    assert client.delete(f"/api/regulation-documents/{uploaded['id']}").status_code == 204
    assert (
        client.get(f"/api/project-types/{type_id}/regulations/reviewer").json()["documents"] == []
    )
