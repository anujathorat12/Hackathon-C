import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app

FORMAT_EXT = {"DOCX": ".docx", "PPT": ".pptx", "PDF": ".pdf", "MD": ".md"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("fmt", list(FORMAT_EXT))
def test_workspace_to_deliverable_flow(client, fmt):
    """Workspace → streamed agents → human approval → document compile → download."""
    ws_id = client.post("/api/v1/workspaces", json={
        "title": f"Integration {fmt}", "description": "End-to-end integration check.", "target_format": fmt,
    }).json()["workspace_id"]

    with client.websocket_connect(f"/api/v1/workspaces/{ws_id}/stream") as ws:
        events = []
        while not events or events[-1]["status"] != "WAITING_FOR_REVIEW":
            events.append(ws.receive_json())

    completed = [e["agent_name"] for e in events if e["status"] != "RUNNING"]
    assert completed[0] == "Requirement Analysis Agent"
    assert completed[-1] == "Content Review Agent"
    assert len(events[-1]["payload"]["refined_content"]) > 100
    assert client.get(f"/api/v1/workspaces/{ws_id}/status").json()["status"] == "WAITING_FOR_REVIEW"

    edited = events[-1]["payload"]["refined_content"] + "\n\n## Reviewer Notes\nApproved by a human reviewer.\n"
    res = client.post(f"/api/v1/workspaces/{ws_id}/approve", json={"content_markdown": edited})
    assert res.status_code == 200, res.text
    deliverable = res.json()
    assert deliverable["file_name"].endswith(FORMAT_EXT[fmt])
    assert deliverable["wcag_compliant"] is True

    download = client.get(deliverable["download_url"])
    assert download.status_code == 200
    assert len(download.content) == deliverable["file_size_bytes"]

    run = client.get(f"/api/v1/workspaces/{ws_id}/run").json()
    assert run["status"] == "COMPLETED"
    assert run["refined_content"] == edited


def test_export_is_scoped_to_topic(client):
    ws_id = client.post("/api/v1/workspaces", json={
        "title": "Empty", "description": "No run yet.", "target_format": "DOCX",
    }).json()["workspace_id"]
    assert client.get(f"/api/v1/workspaces/{ws_id}/export").status_code == 404
    assert client.post(f"/api/v1/workspaces/{ws_id}/approve", json={}).status_code == 409


def _run_to_review(client, ws_id):
    with client.websocket_connect(f"/api/v1/workspaces/{ws_id}/stream") as ws:
        events = []
        while not events or events[-1]["status"] != "WAITING_FOR_REVIEW":
            events.append(ws.receive_json())
    return events


def test_versions_and_restart_recovery(client):
    """Each approval is a new version, and a delivered topic is restored after a server restart."""
    from app.api import workspaces
    ws_id = client.post("/api/v1/workspaces", json={
        "title": "Versioned Doc", "description": "Versioning check.", "target_format": "MD",
    }).json()["workspace_id"]
    content = _run_to_review(client, ws_id)[-1]["payload"]["refined_content"]

    v1 = client.post(f"/api/v1/workspaces/{ws_id}/approve", json={"content_markdown": content}).json()
    v2 = client.post(f"/api/v1/workspaces/{ws_id}/approve", json={"content_markdown": content + "\n\n## Added\nMore.\n"}).json()
    assert (v1["version"], v2["version"]) == ("1.0", "2.0")
    assert v1["file_name"] != v2["file_name"] and v2["file_name"].endswith("_v2.0.md")
    assert v1["change_note"] == "First approved version" and v2["change_note"] == "Manual edits to the content"

    workspaces._runs.clear()  # simulate a restart: in-memory run state is gone
    run = client.get(f"/api/v1/workspaces/{ws_id}/run").json()
    assert [d["version"] for d in run["deliverables"]] == ["1.0", "2.0"]
    assert run["refined_content"].endswith("More.\n")
    assert client.get(v1["download_url"]).status_code == 200


def test_sources_ground_the_run(client):
    ws_id = client.post("/api/v1/workspaces", json={
        "title": "Grounded Doc", "description": "Uses an uploaded source.", "target_format": "DOCX",
    }).json()["workspace_id"]
    text = ("The pilot programme reduced onboarding time from 14 days to 6 days across three offices. "
            "Mentors met new joiners weekly and satisfaction scores rose to 4.6 out of 5.") * 3
    up = client.post(f"/api/v1/workspaces/{ws_id}/sources", files={"file": ("pilot_report.txt", text.encode(), "text/plain")})
    assert up.status_code == 200 and up.json()["passages"] >= 1
    assert client.post(f"/api/v1/workspaces/{ws_id}/sources", files={"file": ("x.exe", b"bin")}).status_code == 415
    assert [s["file_name"] for s in client.get(f"/api/v1/workspaces/{ws_id}/sources").json()] == ["pilot_report.txt"]

    review = _run_to_review(client, ws_id)[-1]["payload"]
    assert review["citation_check"] is not None and "uncited_figures" in review["citation_check"]
    research = next(e for e in _run_to_review(client, ws_id) if e["agent_name"] == "Research & Enrichment Agent" and e["status"] == "COMPLETED")
    assert research["payload"]["from_user_sources"] is True


def test_revise_reports_unavailable_ai_clearly(client):
    ws_id = client.post("/api/v1/workspaces", json={"title": "R", "description": "r", "target_format": "MD"}).json()["workspace_id"]
    res = client.post(f"/api/v1/workspaces/{ws_id}/revise", json={"content_markdown": "# R\n\n## A\nText.", "instruction": "Shorter"})
    assert res.status_code == 503  # tests run offline, so the AI is unavailable
    assert client.post(f"/api/v1/workspaces/{ws_id}/revise", json={"content_markdown": "# R", "instruction": "  "}).status_code == 422
