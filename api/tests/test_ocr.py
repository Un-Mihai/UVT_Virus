import asyncio
import json
import shutil
from typing import Any

import pytest

from app.config import Settings
from app.ocr import RecognizedPage, RecognizedWord, build_ocr_engine
from app.ocr.pages import to_pdf_points
from app.ocr.render import render_page_png
from app.ocr.tesseract import TesseractEngine, parse_tsv
from app.pdf import locate_words, read_pdf
from tests.conftest import FakeOcrEngine, FakeProvider, MakeClient, as_user, prompt_of, run_sql
from tests.flows import add_rule, create_project, create_project_type, upload, verify
from tests.pdf_factory import make_pdf, make_scan
from tests.test_romanian import make_cnp

CNP = make_cnp("190010112345")  # synthetic
CUI_LINE = "Beneficiar: Alfa Construct SRL, CUI RO 361821"
SCAN_LINES = ["Contract de finantare (synthetic scan)", CUI_LINE, f"Reprezentant: CNP {CNP}"]

TSV = "\n".join(
    [
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext",
        "1\t1\t0\t0\t0\t0\t0\t0\t2480\t3508\t-1\t",
        "4\t1\t1\t1\t1\t0\t300\t300\t900\t40\t-1\t",
        "5\t1\t1\t1\t1\t1\t300\t300\t250\t40\t96.5\tContract",
        "5\t1\t1\t1\t1\t2\t570\t300\t60\t40\t91\tnr.",
        "5\t1\t1\t1\t2\t1\t300\t360\t200\t40\t40\tCUI",
        "5\t1\t1\t1\t2\t2\t520\t360\t10\t40\t-1\t ",
    ]
)


def test_tsv_gives_words_with_boxes_and_lines() -> None:
    page = parse_tsv(TSV)

    assert page.text == "Contract nr.\nCUI"
    assert [(word.text, word.confidence) for word in page.words] == [
        ("Contract", 0.965),
        ("nr.", 0.91),
        ("CUI", 0.4),
    ]
    assert (page.words[0].x0, page.words[0].bottom) == (300, 340)


def test_pixels_become_pdf_points() -> None:
    page = RecognizedPage("Ţară", [RecognizedWord("Ţară", 300, 600, 600, 650, 0.8)])

    read = to_pdf_points(page, dpi=300)

    assert read.text == "Țară"  # legacy cedilla normalised like the text layer
    word = read.words[0]
    assert (word.x0, word.top, word.x1, word.bottom, word.confidence) == (72, 144, 144, 156, 0.8)
    assert read.confidence == 0.8


def test_ocr_can_be_switched_off() -> None:
    assert build_ocr_engine(Settings(_env_file=None, ocr_engine="none")) is None
    assert build_ocr_engine(Settings(_env_file=None, ocr_engine="tesseract")) is not None


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_tesseract_reads_a_scan_where_its_text_layer_would_be() -> None:
    lines = ["Contract de finantare nr. 12/2026", "Beneficiar: Alfa Construct SRL"]
    scan = make_scan(lines)
    assert read_pdf(scan)[0].is_scan

    async def read() -> Any:
        png = await render_page_png(scan, 1, dpi=300)
        return to_pdf_points(await TesseractEngine("ron+eng", 60).recognize(png, 300), 300)

    read_page = asyncio.run(read())

    assert "Beneficiar" in read_page.text
    expected = locate_words(read_pdf(make_pdf(lines))[0].words, "Beneficiar")
    found = locate_words(read_page.words, "Beneficiar")
    assert expected
    assert found
    for side in ("x0", "top", "x1", "bottom"):
        assert abs(getattr(found[0], side) - getattr(expected[0], side)) < 3, side


def scan_facts(body: dict[str, Any]) -> str:
    assert CNP not in prompt_of(body), "the model only sees the masked CNP"
    party = {"name": "Alfa Construct SRL", "cui": "RO 361821", "role": None, "quote": CUI_LINE}
    return json.dumps(
        {
            "document_type": "contract",
            "parties": [party],
            "ibans": [],
            "amounts": [],
            "dates": [],
        }
    )


def test_scans_are_read_after_upload(make_client: MakeClient) -> None:
    ocr = FakeOcrEngine(SCAN_LINES, confidence=0.8)
    client = make_client(ocr=ocr)
    project_id = create_project(client, create_project_type(client))

    document_id = upload(client, project_id, "scan.pdf", ["(image only)"], scan=True)

    document = client.get(f"/api/projects/{project_id}").json()["documents"][0]
    page = document["pages"][0]
    assert (page["source"], page["ocr_status"], page["ocr_confidence"]) == ("ocr", "done", 0.8)
    assert document["reading_stalled"] is False
    assert ocr.calls == 1
    identifiers = run_sql(
        "SELECT masked, valid FROM personal_identifiers WHERE document_id = :id", id=document_id
    )
    assert [(row.masked, row.valid) for row in identifiers] == [(f"1*********{CNP[-3:]}", True)]


def test_findings_on_ocr_text_are_only_as_sure_as_the_reading(make_client: MakeClient) -> None:
    provider = FakeProvider(answers={"PageFacts": scan_facts})
    client = make_client(provider, ocr=FakeOcrEngine(SCAN_LINES, confidence=0.8))
    type_id = create_project_type(client)
    for scope, code in (("client", "C-CUI"), ("reviewer", "R-CUI")):
        add_rule(
            client, type_id, scope, code=code, title=code, kind="check",
            check_id="identifiers.cui_valid",
        )  # fmt: skip
    project_id = create_project(client, type_id)
    upload(client, project_id, "scan.pdf", ["(image only)"], scan=True)

    as_user(client, "client")
    client_report = verify(client, project_id)
    client.post(f"/api/projects/{project_id}/submit")
    as_user(client, "reviewer")
    reviewer_report = verify(client, project_id)

    # 0.8 OCR confidence: under the client's 0.85 threshold, over the reviewer's 0.55.
    assert client_report["findings"] == []
    [finding] = reviewer_report["findings"]
    assert (finding["rule_code"], finding["ocr"], finding["confidence"]) == ("R-CUI", True, 0.8)
    assert finding["rects"], "the misread value is highlighted on the scan"


def test_checks_wait_until_scans_are_read(make_client: MakeClient) -> None:
    client = make_client(ocr=FakeOcrEngine())
    project_id = create_project(client, create_project_type(client))
    upload(client, project_id, "scan.pdf", ["(image only)"], scan=True)
    run_sql("UPDATE document_pages SET ocr_status = 'pending', ocr_updated_at = now()")

    as_user(client, "client")
    waiting = client.post(f"/api/projects/{project_id}/verifications")
    run_sql("UPDATE document_pages SET ocr_updated_at = now() - interval '20 minutes'")
    document = client.get(f"/api/projects/{project_id}").json()["documents"][0]

    assert waiting.status_code == 409
    assert "still being read" in waiting.json()["detail"]
    assert document["reading_stalled"] is True
    assert client.post(f"/api/projects/{project_id}/verifications").status_code == 202


def test_failed_pages_can_be_read_again(make_client: MakeClient) -> None:
    failing = make_client(ocr=FakeOcrEngine(fail=True))
    project_id = create_project(failing, create_project_type(failing))
    document_id = upload(failing, project_id, "scan.pdf", ["(image only)"], scan=True)
    page = failing.get(f"/api/projects/{project_id}").json()["documents"][0]["pages"][0]
    assert (page["source"], page["ocr_status"]) == ("none", "failed")

    working = as_user(make_client(ocr=FakeOcrEngine(["Read on the second try"])), "client")
    again = working.post(f"/api/projects/{project_id}/documents/{document_id}/read-scans")
    page = working.get(f"/api/projects/{project_id}").json()["documents"][0]["pages"][0]

    assert again.status_code == 202
    assert (page["source"], page["ocr_status"]) == ("ocr", "done")
    assert (
        working.post(f"/api/projects/{project_id}/documents/{document_id}/read-scans").status_code
        == 409
    )


def test_without_ocr_scanned_pages_are_flagged_as_unchecked(make_client: MakeClient) -> None:
    client = make_client()  # OCR_ENGINE=none
    project_id = create_project(client, create_project_type(client))
    document_id = upload(client, project_id, "scan.pdf", ["(image only)"], scan=True)

    as_user(client, "client")
    page = client.get(f"/api/projects/{project_id}").json()["documents"][0]["pages"][0]
    [finding] = verify(client, project_id)["findings"]

    assert page["ocr_status"] == "unavailable"
    assert finding["rule_code"] == "extraction.unreadable_page"
    assert "OCR" in finding["reason"]["en"]
    assert "OCR" in finding["reason"]["ro"]
    assert (
        client.post(f"/api/projects/{project_id}/documents/{document_id}/read-scans").status_code
        == 503
    )


def test_status_reports_whether_scans_can_be_read(make_client: MakeClient) -> None:
    assert make_client().get("/api/ocr/status").json()["engine"] == "none"
    status = make_client(ocr=FakeOcrEngine()).get("/api/ocr/status").json()
    assert (status["engine"], status["available"]) == ("fake", True)


def test_scanned_regulations_are_read_into_their_text(make_client: MakeClient) -> None:
    client = make_client(ocr=FakeOcrEngine(["Art. 5 Garantia minima este 10%"]))
    type_id = create_project_type(client)

    uploaded = client.post(
        f"/api/project-types/{type_id}/regulations/client/documents",
        files={"file": ("rules.pdf", make_scan(["(image only)"]), "application/pdf")},
    ).json()
    listed = client.get(f"/api/project-types/{type_id}/regulations/client").json()

    assert uploaded["scanned_pages"] == 1
    assert listed["documents"][0]["ocr_status"] == "done"
    [row] = run_sql("SELECT text FROM regulation_documents")
    assert "Garantia minima este 10%" in row.text
