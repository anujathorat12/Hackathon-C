import os
import uuid
import asyncio
import datetime
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.database.mongodb import get_database
from app.orchestration.pipeline_runner import run_pipeline_async

router = APIRouter()

ROOT_DIR = Path(__file__).resolve().parents[3]
TEMPLATES_DIR = ROOT_DIR / "storage" / "templates"
OUTPUTS_DIR = ROOT_DIR / "storage" / "outputs"

FORMAT_MEDIA_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".pdf": "application/pdf",
    ".md": "text/markdown",
}


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


# ─── Persistence: MongoDB when available, in-memory otherwise ───────────────────

_mem_workspaces: Dict[str, Dict[str, Any]] = {}
_mem_templates: Dict[str, List[Dict[str, Any]]] = {}

# Live run state per topic (events, refined content, deliverables). Not persisted.
_runs: Dict[str, Dict[str, Any]] = {}


def _run(topic_id: str) -> Dict[str, Any]:
    return _runs.setdefault(topic_id, {"events": [], "refined_content": None, "deliverables": []})


async def _ws_insert(doc: Dict[str, Any]) -> None:
    db = get_database()
    if db is not None:
        await db.topic_workspaces.insert_one(doc)
    else:
        _mem_workspaces[doc["_id"]] = doc


async def _ws_all() -> List[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        docs = await db.topic_workspaces.find().sort("created_at", 1).to_list(length=100)
    else:
        docs = sorted(_mem_workspaces.values(), key=lambda d: d["created_at"])
    return [_serialize(d) for d in docs]


async def _ws_get(topic_id: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        return await db.topic_workspaces.find_one({"_id": topic_id})
    return _mem_workspaces.get(topic_id)


async def _ws_update(topic_id: str, fields: Dict[str, Any]) -> None:
    fields = {**fields, "updated_at": _now()}
    db = get_database()
    if db is not None:
        await db.topic_workspaces.update_one({"_id": topic_id}, {"$set": fields})
    elif topic_id in _mem_workspaces:
        _mem_workspaces[topic_id].update(fields)


async def _ws_delete(topic_id: str) -> None:
    db = get_database()
    if db is not None:
        await db.topic_workspaces.delete_one({"_id": topic_id})
        await db.reference_templates.delete_many({"topic_id": topic_id})
    _mem_workspaces.pop(topic_id, None)
    _mem_templates.pop(topic_id, None)
    _runs.pop(topic_id, None)


async def _tpl_insert(doc: Dict[str, Any]) -> None:
    db = get_database()
    if db is not None:
        await db.reference_templates.insert_one(doc)
    else:
        _mem_templates.setdefault(doc["topic_id"], []).append(doc)


async def _tpl_list(topic_id: str) -> List[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        docs = await db.reference_templates.find({"topic_id": topic_id}).sort("created_at", 1).to_list(length=50)
    else:
        docs = list(_mem_templates.get(topic_id, []))
    return [_serialize(d) for d in docs]


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in doc.items() if k != "_id"}
    out["id"] = doc["_id"]
    for k, v in out.items():
        if isinstance(v, datetime.datetime):
            out[k] = v.isoformat() + "Z"
    return out


# ─── Workspaces ─────────────────────────────────────────────────────────────────

class WorkspaceCreate(BaseModel):
    title: str
    description: str
    target_format: str
    user_instructions: Optional[str] = None


class ApproveRequest(BaseModel):
    content_markdown: Optional[str] = None


@router.post("")
async def create_workspace(workspace: WorkspaceCreate):
    workspace_id = str(uuid.uuid4())
    await _ws_insert({
        "_id": workspace_id,
        "title": workspace.title,
        "description": workspace.description,
        "target_format": workspace.target_format.upper(),
        "user_instructions": workspace.user_instructions,
        "status": "CREATED",
        "created_at": _now(),
        "updated_at": _now(),
    })
    return {"workspace_id": workspace_id, "status": "CREATED"}


@router.get("")
async def get_workspaces():
    return await _ws_all()


@router.delete("/{topic_id}")
async def delete_workspace(topic_id: str):
    await _ws_delete(topic_id)
    return {"deleted": topic_id}


# ─── Templates (upload → Reference Analysis) ────────────────────────────────────

@router.post("/{topic_id}/templates")
async def upload_template(topic_id: str, file: UploadFile = File(...)):
    topic_dir = TEMPLATES_DIR / topic_id
    topic_dir.mkdir(parents=True, exist_ok=True)
    file_name = os.path.basename(file.filename or "template")
    file_path = topic_dir / file_name
    file_path.write_bytes(await file.read())

    guidance = None
    try:
        from app.agents.document.reference_agent import ReferenceAnalysisAgent
        profile = await asyncio.to_thread(ReferenceAnalysisAgent().analyze_template, str(file_path))
        guidance = profile.model_dump()
    except Exception as e:
        print(f"[Templates] Reference analysis failed for {file_name}: {e}")

    template_id = str(uuid.uuid4())
    doc = {
        "_id": template_id,
        "topic_id": topic_id,
        "file_name": file_name,
        "file_type": file_name.rsplit(".", 1)[-1].upper(),
        "storage_path": str(file_path),
        "file_size_bytes": file_path.stat().st_size,
        "guidance": guidance,
        "created_at": _now(),
    }
    await _tpl_insert(doc)
    return _serialize(doc)


@router.get("/{topic_id}/templates")
async def list_templates(topic_id: str):
    return await _tpl_list(topic_id)


# ─── Pipeline (cognitive agents, streamed) ──────────────────────────────────────

@router.post("/{topic_id}/generate")
async def generate_document(topic_id: str):
    await _ws_update(topic_id, {"status": "PROCESSING"})
    return {"task_id": f"job-{topic_id}", "status": "PROCESSING"}


@router.get("/{topic_id}/status")
async def get_status(topic_id: str):
    ws = await _ws_get(topic_id)
    return {"status": ws.get("status", "IDLE") if ws else "UNKNOWN"}


@router.get("/{topic_id}/run")
async def get_run(topic_id: str):
    """Full run snapshot so the UI can restore a workspace when switching tabs."""
    ws = await _ws_get(topic_id)
    run = _runs.get(topic_id, {"events": [], "refined_content": None, "deliverables": []})
    return {
        "status": ws.get("status", "IDLE") if ws else "UNKNOWN",
        "events": run["events"],
        "refined_content": run["refined_content"],
        "deliverables": run["deliverables"],
    }


@router.websocket("/{topic_id}/stream")
async def websocket_endpoint(websocket: WebSocket, topic_id: str):
    await websocket.accept()

    ws = await _ws_get(topic_id) or {}
    templates = await _tpl_list(topic_id)
    template_file_path = templates[-1]["storage_path"] if templates else None

    run = _run(topic_id)
    run.update({"events": [], "refined_content": None})
    await _ws_update(topic_id, {"status": "PROCESSING"})

    try:
        async for event in run_pipeline_async(
            topic_id=topic_id,
            title=ws.get("title", "Autonomous Document"),
            description=ws.get("description", ""),
            target_format=ws.get("target_format", "DOCX"),
            user_instructions=ws.get("user_instructions"),
            template_file_path=template_file_path,
        ):
            data = event.model_dump()
            if event.agent_name == "Content Review Agent" and event.status == "WAITING_FOR_REVIEW":
                run["refined_content"] = event.payload.get("refined_content", "")
            run["events"].append(data)
            await websocket.send_json(data)

        await _ws_update(topic_id, {"status": "WAITING_FOR_REVIEW"})
        await websocket.close()

    except WebSocketDisconnect:
        print(f"Client disconnected for topic {topic_id}")
    except Exception as e:
        print(f"Pipeline error: {e}")
        await _ws_update(topic_id, {"status": "FAILED"})
        try:
            await websocket.send_json({
                "topic_id": topic_id, "agent_name": "System", "status": "FAILED",
                "progress_percent": 0, "message": str(e), "payload": {}, "timestamp": _now(),
            })
        except Exception:
            pass


@router.get("/{topic_id}/content")
async def get_refined_content(topic_id: str):
    run = _runs.get(topic_id)
    if not run or not run.get("refined_content"):
        raise HTTPException(status_code=404, detail="No refined content yet. Run the pipeline first.")
    return {"refined_content": run["refined_content"]}


# ─── Human-in-the-loop approval → document compilation ──────────────────────────

@router.post("/{topic_id}/approve")
async def approve_and_compile(topic_id: str, body: ApproveRequest):
    from app.agents.document.reference_agent import ReferenceAnalysisAgent
    from app.agents.document.format_agent import FormatGenerationAgent
    from app.shared.schemas.template_models import DocumentCompileRequest

    ws = await _ws_get(topic_id)
    if not ws:
        raise HTTPException(
            status_code=404,
            detail="This topic no longer exists on the server (it was probably restarted). "
                   "Refresh the page, create the topic again and relaunch.",
        )

    run = _run(topic_id)
    content = body.content_markdown or run.get("refined_content")
    if not content:
        raise HTTPException(status_code=409, detail="Nothing to compile. Run the pipeline first.")
    run["refined_content"] = content

    templates = await _tpl_list(topic_id)
    template_file_path = templates[-1]["storage_path"] if templates else None
    await _ws_update(topic_id, {"status": "COMPILING"})

    def compile_sync():
        analyzer = ReferenceAnalysisAgent()
        try:
            guidance = analyzer.analyze_template(template_file_path)
        except Exception as e:
            # A template that can't be parsed should not block delivery; use the default theme.
            print(f"[Approve] Template analysis failed ({e}); using default theme.", flush=True)
            guidance = analyzer.analyze_template(None)
        request = DocumentCompileRequest(
            topic_id=topic_id,
            title=ws["title"],
            target_format=ws["target_format"],
            refined_content_markdown=content,
            template_guidance=guidance,
            output_directory=str(OUTPUTS_DIR / topic_id),
        )
        return FormatGenerationAgent().compile_document(request)

    try:
        result = await asyncio.to_thread(compile_sync)
    except Exception as e:
        traceback.print_exc()
        result = None
        error = f"{type(e).__name__}: {e}"
    else:
        error = None if result.success else (result.error_message or "Compilation failed.")

    if error:
        # Keep the reviewed draft so the user can fix it and approve again.
        await _ws_update(topic_id, {"status": "WAITING_FOR_REVIEW"})
        raise HTTPException(status_code=500, detail=f"Document compilation failed — {error}")

    page_count = result.page_or_slide_count
    if result.format == "PPT":
        try:
            from pptx import Presentation
            page_count = len(Presentation(result.file_path).slides)
        except Exception:
            pass

    deliverable = {
        "file_name": result.file_name,
        "format": result.format,
        "file_size_bytes": result.file_size_bytes,
        "page_or_slide_count": page_count,
        "wcag_compliant": result.wcag_compliant,
        "accessibility_report": result.accessibility_report.model_dump() if result.accessibility_report else None,
        "download_url": f"/api/v1/workspaces/{topic_id}/export?file={result.file_name}",
        "compiled_at": _now(),
    }
    run["deliverables"] = [d for d in run["deliverables"] if d["file_name"] != result.file_name] + [deliverable]
    run["events"].append({
        "topic_id": topic_id,
        "agent_name": "Format Generation Agent",
        "status": "COMPLETED",
        "progress_percent": 100,
        "message": f"Compiled {result.file_name} — WCAG 2.2 AA {'passed' if result.wcag_compliant else 'needs attention'}.",
        "payload": deliverable,
        "timestamp": _now(),
    })
    await _ws_update(topic_id, {"status": "COMPLETED"})
    return deliverable


@router.get("/{topic_id}/deliverables")
async def list_deliverables(topic_id: str):
    topic_dir = OUTPUTS_DIR / topic_id
    if not topic_dir.is_dir():
        return []
    return [
        {
            "file_name": f.name,
            "file_size_bytes": f.stat().st_size,
            "download_url": f"/api/v1/workspaces/{topic_id}/export?file={f.name}",
        }
        for f in sorted(topic_dir.iterdir()) if f.is_file()
    ]


@router.get("/{topic_id}/export")
async def export_document(topic_id: str, file: Optional[str] = None):
    """Serve this topic's compiled deliverable (latest one unless a file name is given)."""
    topic_dir = OUTPUTS_DIR / topic_id
    if topic_dir.is_dir():
        if file:
            candidate = topic_dir / os.path.basename(file)
            files = [candidate] if candidate.is_file() else []
        else:
            files = sorted((f for f in topic_dir.iterdir() if f.is_file()), key=lambda f: f.stat().st_mtime)
        if files:
            target = files[-1]
            return FileResponse(
                target,
                filename=target.name,
                media_type=FORMAT_MEDIA_TYPES.get(target.suffix.lower(), "application/octet-stream"),
            )
    raise HTTPException(status_code=404, detail="No compiled deliverable found for this workspace.")
