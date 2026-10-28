"""API steps the tests repeat: an admin sets up a project type, a client applies."""

from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import as_user
from tests.pdf_factory import make_pdf, make_scan

FORM = {
    "applicant_name": "Alfa Construct SRL",
    "applicant_cui": "RO 361820",
    "legal_representative_name": "Ion Pop",
    "requested_amount": "1.000,00",
    "start_date": "01.01.2026",
    "end_date": "31.12.2026",
}


def create_project_type(client: TestClient, code: str = "infra") -> int:
    as_user(client, "admin")
    response = client.post("/api/project-types", json={"code": code, "name": "Infrastructure"})
    assert response.status_code == 201, response.text
    project_id: int = response.json()["id"]
    return project_id


def add_rule(client: TestClient, project_type_id: int, scope: str, **rule: Any) -> dict[str, Any]:
    as_user(client, "admin")
    response = client.post(
        f"/api/project-types/{project_type_id}/regulations/{scope}/rules", json=rule
    )
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def create_project(
    client: TestClient, project_type_id: int, form: dict[str, Any] | None = None
) -> int:
    as_user(client, "client")
    response = client.post(
        "/api/projects",
        json={"project_type_id": project_type_id, "title": "Bridge repair", "form": form or FORM},
    )
    assert response.status_code == 201, response.text
    project_id: int = response.json()["id"]
    return project_id


def upload(
    client: TestClient, project_id: int, name: str, *pages: list[str], scan: bool = False
) -> int:
    """Uploads a PDF of `pages` as the client; `scan` makes every page a picture of its text."""
    as_user(client, "client")
    content = make_scan(*pages) if scan else make_pdf(*pages)
    response = client.post(
        f"/api/projects/{project_id}/documents",
        files={"file": (name, content, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    document_id: int = response.json()["id"]
    return document_id


def verify(client: TestClient, project_id: int) -> dict[str, Any]:
    """Runs the check as the client's current user and returns the finished report."""
    started = client.post(f"/api/projects/{project_id}/verifications")
    assert started.status_code == 202, started.text
    report: dict[str, Any] = client.get(f"/api/projects/{project_id}/verifications/latest").json()
    assert report["run"]["status"] == "completed", report["run"]
    return report
