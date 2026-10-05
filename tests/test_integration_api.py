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
    """Module A workspace → Module B streamed agents → human approval → Module C compile → download."""
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
