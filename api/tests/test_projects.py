from fastapi.testclient import TestClient

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


def test_reviewers_see_who_applied_and_clients_see_when_review_starts(
    make_client: MakeClient,
) -> None:
    client = make_client()
    project_id = create_project(client, create_project_type(client))
    upload(client, project_id, "contract.pdf", ["Contract"])

    drafts = client.get("/api/projects").json()
    client.post(f"/api/projects/{project_id}/submit")
    waiting = client.get(f"/api/projects/{project_id}").json()
    as_user(client, "reviewer")
    applicants = client.get("/api/projects").json()
    assert client.post(f"/api/projects/{project_id}/verifications").status_code == 202
    as_user(client, "client")
    started = client.get("/api/projects").json()

    assert [p["in_review"] for p in drafts] == [False]
    assert (waiting["status"], waiting["in_review"]) == ("submitted", False)
    assert [(p["owner_name"], p["applicant_name"]) for p in applicants] == [
        ("client", "Alfa Construct SRL")
    ]
    assert [p["in_review"] for p in started] == [True]


def submitted_project(client: TestClient) -> int:
    project_id = create_project(client, create_project_type(client))
    upload(client, project_id, "contract.pdf", ["Contract"])
    client.post(f"/api/projects/{project_id}/submit")
    return project_id


def test_reviewer_approves_and_the_client_sees_it(make_client: MakeClient) -> None:
    client = make_client()
    project_id = submitted_project(client)
    url = f"/api/projects/{project_id}/verdict"

    as_user(client, "client")
    by_client = client.put(url, json={"verdict": "approved"})
    as_user(client, "reviewer")
    approved = client.put(url, json={"verdict": "approved", "note": "  All in order.  "})
    as_user(client, "client")
    seen = client.get(f"/api/projects/{project_id}").json()

    assert by_client.status_code == 403
    assert approved.status_code == 204
    assert (seen["status"], seen["verdict"], seen["verdict_note"]) == (
        "submitted",
        "approved",
        "All in order.",
    )
    assert client.patch(f"/api/projects/{project_id}", json={"title": "x"}).status_code == 409


def test_requested_changes_return_the_project_until_it_is_submitted_again(
    make_client: MakeClient,
) -> None:
    client = make_client()
    project_id = submitted_project(client)
    url = f"/api/projects/{project_id}/verdict"

    as_user(client, "reviewer")
    client.post(f"/api/projects/{project_id}/verifications")
    without_note = client.put(url, json={"verdict": "changes_requested", "note": " "})
    sent_back = client.put(url, json={"verdict": "changes_requested", "note": "Sign the contract."})
    hidden = client.get("/api/projects").json()
    reviewer_after = client.put(url, json={"verdict": "approved"})

    as_user(client, "client")
    returned = client.get(f"/api/projects/{project_id}").json()
    edited = client.patch(f"/api/projects/{project_id}", json={"title": "Fixed"})
    resubmitted = client.post(f"/api/projects/{project_id}/submit").json()
    as_user(client, "reviewer")
    waiting = client.get("/api/projects").json()

    assert without_note.status_code == 422
    assert sent_back.status_code == 204
    assert hidden == []
    assert reviewer_after.status_code == 404
    assert (returned["status"], returned["verdict"]) == ("draft", "changes_requested")
    assert returned["verdict_note"] == "Sign the contract."
    assert edited.status_code == 200
    assert (resubmitted["verdict"], resubmitted["in_review"]) == (None, False)
    assert [(p["verdict"], p["in_review"]) for p in waiting] == [(None, False)]
