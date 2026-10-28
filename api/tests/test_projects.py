from tests.conftest import MakeClient, as_user, run_sql
from tests.flows import FORM, create_project, create_project_type, upload
from tests.test_romanian import make_cnp


def test_client_applies_uploads_and_submits(make_client: MakeClient) -> None:
    client = make_client()
    project_id = create_project(client, create_project_type(client))
    document_id = upload(client, project_id, "contract.pdf", ["Contract"], ["Annex"])

    project = client.get(f"/api/projects/{project_id}").json()
    submitted = client.post(f"/api/projects/{project_id}/submit")

    assert project["status"] == "draft"
    assert [(d["id"], d["page_count"]) for d in project["documents"]] == [(document_id, 2)]
    assert submitted.json()["status"] == "submitted"
    assert client.patch(f"/api/projects/{project_id}", json={"title": "Changed"}).status_code == 409
    file = client.get(f"/api/projects/{project_id}/documents/{document_id}/file")
    assert file.headers["content-type"] == "application/pdf"
    assert file.content.startswith(b"%PDF-")


def test_cnp_in_the_form_is_stored_only_masked(make_client: MakeClient) -> None:
    client = make_client()
    cnp = make_cnp("190010112345")
    project_id = create_project(
        client, create_project_type(client), FORM | {"legal_representative_cnp": cnp}
    )

    form = client.get(f"/api/projects/{project_id}").json()["form"]

    assert "legal_representative_cnp" not in form
    assert form["legal_representative_cnp_masked"] == f"{cnp[0]}*********{cnp[-3:]}"
    assert cnp not in str(form)


def test_editing_without_the_cnp_keeps_the_one_given(make_client: MakeClient) -> None:
    client = make_client()
    cnp = make_cnp("190010112345")
    project_id = create_project(
        client, create_project_type(client), FORM | {"legal_representative_cnp": cnp}
    )

    edited = client.patch(
        f"/api/projects/{project_id}", json={"form": FORM | {"applicant_name": "Beta SA"}}
    ).json()

    assert edited["form"]["applicant_name"] == "Beta SA"
    assert edited["form"]["legal_representative_cnp_masked"] == f"{cnp[0]}*********{cnp[-3:]}"
    rows = run_sql("SELECT count(*) AS n FROM personal_identifiers WHERE document_id IS NULL")
    assert rows[0].n == 1


def test_uploads_must_be_pdfs_within_the_size_limit(make_client: MakeClient) -> None:
    client = make_client()
    project_id = create_project(client, create_project_type(client))
    url = f"/api/projects/{project_id}/documents"

    text_file = client.post(url, files={"file": ("notes.txt", b"hello", "text/plain")})
    tiny_limit = make_client(max_upload_mb=0)
    as_user(tiny_limit, "client")
    too_large = tiny_limit.post(url, files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")})

    assert text_file.status_code == 415
    assert too_large.status_code == 413


def test_projects_are_private_to_their_owner_until_submitted(make_client: MakeClient) -> None:
    client = make_client()
    project_id = create_project(client, create_project_type(client))

    as_user(client, "client-2")
    assert client.get(f"/api/projects/{project_id}").status_code == 404
    assert client.get("/api/projects").json() == []
    as_user(client, "reviewer")
    assert client.get(f"/api/projects/{project_id}").status_code == 404
    assert client.get("/api/projects").json() == []
    assert client.post("/api/projects", json={}).status_code == 403
    as_user(client, "admin")
    assert client.get("/api/projects").status_code == 403

    as_user(client, "client")
    assert client.post(f"/api/projects/{project_id}/submit").status_code == 409  # no documents
    upload(client, project_id, "contract.pdf", ["Contract"])
    client.post(f"/api/projects/{project_id}/submit")
    as_user(client, "reviewer")
    assert [p["id"] for p in client.get("/api/projects").json()] == [project_id]
    assert client.get(f"/api/projects/{project_id}").status_code == 200
