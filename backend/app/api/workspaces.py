import os
import uuid
import asyncio
import datetime
import shutil
import subprocess
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
SOURCES_DIR = ROOT_DIR / "storage" / "sources"
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
_mem_sources: Dict[str, List[Dict[str, Any]]] = {}

# Live run state per topic (events, refined content, deliverables). Not persisted.
_runs: Dict[str, Dict[str, Any]] = {}


def _run(topic_id: str) -> Dict[str, Any]:
    return _runs.setdefault(topic_id, {"events": [], "refined_content": None, "deliverables": []})


PERSISTED_RUN_KEYS = ("events", "refined_content", "deliverables", "notes_cache", "revisions", "approved_content", "value", "display_title")


async def _load_run(topic_id: str) -> Dict[str, Any]:
    """Run state from memory, or restored from the saved workspace after a server restart."""
    if topic_id not in _runs:
        ws = await _ws_get(topic_id) or {}
        _runs[topic_id] = {"events": [], "refined_content": None, "deliverables": [], **(ws.get("run_state") or {})}
    return _runs[topic_id]


async def _persist_run(topic_id: str) -> None:
    run = _runs.get(topic_id)
    if run is not None:
        state = {k: run.get(k) for k in PERSISTED_RUN_KEYS if run.get(k) is not None}
        state["events"] = (run.get("events") or [])[-80:]
        await _ws_update(topic_id, {"run_state": state})


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
    from app.services.llm_service import llm_service
    llm_service.clear_topic_context(topic_id)
    db = get_database()
    if db is not None:
        await db.topic_workspaces.delete_one({"_id": topic_id})
        await db.reference_templates.delete_many({"topic_id": topic_id})
        await db.source_documents.delete_many({"topic_id": topic_id})
    from app.services.vector_service import vector_service
    vector_service._in_memory_store.pop(topic_id, None)
    _mem_workspaces.pop(topic_id, None)
    _mem_templates.pop(topic_id, None)
    _mem_sources.pop(topic_id, None)
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


async def _src_insert(doc: Dict[str, Any]) -> None:
    db = get_database()
    if db is not None:
        await db.source_documents.insert_one(doc)
    else:
        _mem_sources.setdefault(doc["topic_id"], []).append(doc)


async def _src_list(topic_id: str) -> List[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        docs = await db.source_documents.find({"topic_id": topic_id}).sort("created_at", 1).to_list(length=50)
    else:
        docs = list(_mem_sources.get(topic_id, []))
    return [_serialize(d) for d in docs]


async def _src_delete(topic_id: str, source_id: str) -> Optional[Dict[str, Any]]:
    docs = {d["id"]: d for d in await _src_list(topic_id)}
    doc = docs.get(source_id)
    db = get_database()
    if db is not None:
        await db.source_documents.delete_one({"_id": source_id})
    else:
        _mem_sources[topic_id] = [d for d in _mem_sources.get(topic_id, []) if d["_id"] != source_id]
    return doc


async def _ensure_sources_indexed(topic_id: str) -> int:
    """Re-index a topic's uploaded sources after a restart (the passage index lives in memory)."""
    from app.services.vector_service import vector_service
    from app.services.source_ingest import extract_passages
    sources = await _src_list(topic_id)
    if sources and not vector_service.has_sources(topic_id):
        for src in sources:
            if os.path.exists(src["storage_path"]):
                passages = await asyncio.to_thread(extract_passages, src["storage_path"], src["file_name"])
                vector_service.seed_topic_knowledge(topic_id, passages)
    return len(sources)


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
    language: str = "English"


class ApproveRequest(BaseModel):
    content_markdown: Optional[str] = None


class ReviseRequest(BaseModel):
    content_markdown: str
    instruction: str
    section: Optional[str] = None  # a "## " heading; None revises the whole document


@router.post("")
async def create_workspace(workspace: WorkspaceCreate):
    workspace_id = str(uuid.uuid4())
    await _ws_insert({
        "_id": workspace_id,
        "title": workspace.title,
        "description": workspace.description,
        "target_format": workspace.target_format.upper(),
        "user_instructions": workspace.user_instructions,
        "language": workspace.language or "English",
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


# ─── Source documents (the topic's own knowledge base) ──────────────────────────

@router.post("/{topic_id}/sources")
async def upload_source(topic_id: str, file: UploadFile = File(...)):
    from app.services.vector_service import vector_service
    from app.services.source_ingest import extract_passages, SUPPORTED_SOURCE_TYPES
    file_name = os.path.basename(file.filename or "source")
    if os.path.splitext(file_name)[1].lower() not in SUPPORTED_SOURCE_TYPES:
        raise HTTPException(status_code=415, detail="Sources must be PDF, DOCX, TXT or MD files.")
    topic_dir = SOURCES_DIR / topic_id
    topic_dir.mkdir(parents=True, exist_ok=True)
    path = topic_dir / file_name
    path.write_bytes(await file.read())
    try:
        passages = await asyncio.to_thread(extract_passages, str(path), file_name)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read {file_name}: {e}")
    if not passages:
        raise HTTPException(status_code=422, detail=f"No readable text found in {file_name} (scanned PDFs need OCR first).")
    await _ensure_sources_indexed(topic_id)
    vector_service.remove_source(topic_id, file_name)
    vector_service.seed_topic_knowledge(topic_id, passages)
    doc = {
        "_id": str(uuid.uuid4()),
        "topic_id": topic_id,
        "file_name": file_name,
        "file_type": file_name.rsplit(".", 1)[-1].upper(),
        "storage_path": str(path),
        "file_size_bytes": path.stat().st_size,
        "passages": len(passages),
        "locations": len({p["label"] for p in passages}),
        "created_at": _now(),
    }
    await _src_insert(doc)
    return _serialize(doc)


@router.get("/{topic_id}/sources")
async def list_sources(topic_id: str):
    return await _src_list(topic_id)


@router.delete("/{topic_id}/sources/{source_id}")
async def delete_source(topic_id: str, source_id: str):
    from app.services.vector_service import vector_service
    doc = await _src_delete(topic_id, source_id)
    if doc:
        vector_service.remove_source(topic_id, doc["file_name"])
    return {"deleted": source_id}


# ─── Pipeline (cognitive agents, streamed) ──────────────────────────────────────

@router.post("/{topic_id}/generate")
async def generate_document(topic_id: str):
    await _ws_update(topic_id, {"status": "PROCESSING"})
    return {"task_id": f"job-{topic_id}", "status": "PROCESSING"}


@router.get("/stats/summary")
async def stats_summary():
    """Totals across all workspaces for the value meter on the home page."""
    runs = [w.get("value") for w in await _ws_all() if w.get("value")]
    return {
        "documents": len(runs),
        "manual_minutes_saved": round(sum(max(0.0, v["manual_minutes"] - v["seconds"] / 60) for v in runs)),
        "cost_usd": round(sum(v["cost_usd"] for v in runs), 4),
        "cost_inr": round(sum(v["cost_inr"] for v in runs), 2),
        "avg_seconds": round(sum(v["seconds"] for v in runs) / len(runs), 1) if runs else 0,
    }


@router.get("/{topic_id}/status")
async def get_status(topic_id: str):
    ws = await _ws_get(topic_id)
    return {"status": ws.get("status", "IDLE") if ws else "UNKNOWN"}


@router.get("/{topic_id}/run")
async def get_run(topic_id: str):
    """Full run snapshot so the UI can restore a workspace when switching tabs."""
    ws = await _ws_get(topic_id)
    run = await _load_run(topic_id)
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
    await _ensure_sources_indexed(topic_id)
    await _ws_update(topic_id, {"status": "PROCESSING"})

    try:
        async for event in run_pipeline_async(
            topic_id=topic_id,
            title=ws.get("title", "Autonomous Document"),
            description=ws.get("description", ""),
            target_format=ws.get("target_format", "DOCX"),
            user_instructions=ws.get("user_instructions"),
            language=ws.get("language") or "English",
            template_file_path=template_file_path,
        ):
            data = event.model_dump()
            if event.agent_name == "Planning Agent" and event.status == "COMPLETED":
                # The planner returns the title in the document's language; show that title in the document.
                planned = (event.payload or {}).get("title")
                if (ws.get("language") or "English") != "English" and planned:
                    run["display_title"] = planned
            if event.agent_name == "Content Review Agent" and event.status == "WAITING_FOR_REVIEW":
                run["refined_content"] = event.payload.get("refined_content", "")
                run["value"] = event.payload.get("value")
            run["events"].append(data)
            await websocket.send_json(data)

        # Persist the run's measured value so dashboard totals survive restarts.
        await _ws_update(topic_id, {"status": "WAITING_FOR_REVIEW", "value": run.get("value")})
        await _persist_run(topic_id)
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
    run = await _load_run(topic_id)
    if not run.get("refined_content"):
        raise HTTPException(status_code=404, detail="No refined content yet. Run the pipeline first.")
    return {"refined_content": run["refined_content"]}


# ─── Document compilation (shared by preview and approval) ──────────────────────

async def _load_for_compile(topic_id: str, content_markdown: Optional[str]):
    ws = await _ws_get(topic_id)
    if not ws:
        raise HTTPException(
            status_code=404,
            detail="This topic no longer exists on the server (it was probably restarted). "
                   "Refresh the page, create the topic again and relaunch.",
        )
    run = await _load_run(topic_id)
    content = content_markdown or run.get("refined_content")
    if not content:
        raise HTTPException(status_code=409, detail="Nothing to compile. Run the pipeline first.")
    run["refined_content"] = content
    templates = await _tpl_list(topic_id)
    return ws, run, content, (templates[-1]["storage_path"] if templates else None)


async def _compile(topic_id: str, ws: Dict[str, Any], content: str, template_file_path: Optional[str], output_dir: Path,
                   version: str = "1.0"):
    """Compile the markdown into the workspace's target format. Raises HTTPException with the real cause on failure."""
    from app.agents.document.reference_agent import ReferenceAnalysisAgent
    from app.agents.document.format_agent import FormatGenerationAgent
    from app.shared.schemas.template_models import DocumentCompileRequest, DocumentControlMetadata
    from app.shared.i18n import format_date, labels, smart_title
    language = ws.get("language") or "English"

    speaker_notes = None
    if ws["target_format"] == "PPT":
        from app.agents.cognitive.notes_agent import notes_agent
        try:
            speaker_notes = await asyncio.to_thread(notes_agent.notes_for, content, _run(topic_id).setdefault("notes_cache", {}))
        except Exception as e:
            print(f"[Compile] Speaker notes skipped ({e}).", flush=True)

    def compile_sync():
        analyzer = ReferenceAnalysisAgent()
        try:
            guidance = analyzer.analyze_template(template_file_path)
        except Exception as e:
            # A template that can't be parsed should not block delivery; use the default theme.
            print(f"[Compile] Template analysis failed ({e}); using default theme.", flush=True)
            guidance = analyzer.analyze_template(None)
        request = DocumentCompileRequest(
            topic_id=topic_id,
            title=ws["title"],
            target_format=ws["target_format"],
            refined_content_markdown=content,
            template_guidance=guidance,
            output_directory=str(output_dir),
            speaker_notes=speaker_notes,
            display_title=_run(topic_id).get("display_title") or smart_title(ws["title"]),
            document_control_metadata=DocumentControlMetadata(
                version=version, language=language, date=format_date(language),
                author=labels(language)["authorship_text"],
            ),
        )
        return FormatGenerationAgent().compile_document(request)

    try:
        result = await asyncio.to_thread(compile_sync)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document compilation failed — {type(e).__name__}: {e}")
    if not result.success:
        raise HTTPException(status_code=500, detail=f"Document compilation failed — {result.error_message or 'unknown error'}")
    return result


def _notes_count(result) -> int:
    if result.format != "PPT":
        return 0
    try:
        from pptx import Presentation
        return sum(1 for s in Presentation(result.file_path).slides
                   if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())
    except Exception:
        return 0


def _slide_count(result) -> int:
    if result.format == "PPT":
        try:
            from pptx import Presentation
            return len(Presentation(result.file_path).slides)
        except Exception:
            pass
    return result.page_or_slide_count


def _find_soffice() -> Optional[str]:
    """LibreOffice gives pixel-accurate previews of PPTX/DOCX by converting them to PDF; optional."""
    candidates = [
        shutil.which("soffice"), shutil.which("libreoffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    return next((c for c in candidates if c and os.path.exists(c)), None)


def _convert_to_pdf(path: Path) -> Optional[Path]:
    soffice = _find_soffice()
    if not soffice:
        return None
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(path.parent), str(path)],
            check=True, capture_output=True, timeout=120,
        )
        pdf = path.with_suffix(".pdf")
        return pdf if pdf.exists() else None
    except Exception as e:
        print(f"[Preview] LibreOffice conversion failed ({e}); falling back to in-browser rendering.", flush=True)
        return None


# ─── Ask AI to revise (whole document or one section) ───────────────────────────

@router.post("/{topic_id}/revise")
async def revise_content(topic_id: str, body: ReviseRequest):
    from app.agents.cognitive.revision_agent import revision_agent
    if not body.instruction.strip():
        raise HTTPException(status_code=422, detail="Tell the AI what to change.")
    try:
        revised, summary = await asyncio.to_thread(
            revision_agent.run, body.content_markdown, body.instruction.strip(), body.section
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    run = await _load_run(topic_id)
    run["refined_content"] = revised
    run.setdefault("revisions", []).append({"instruction": body.instruction.strip(), "section": body.section, "at": _now()})
    await _persist_run(topic_id)
    return {"content_markdown": revised, "summary": summary}


# ─── Format-specific preview of the reviewed draft ──────────────────────────────

@router.post("/{topic_id}/preview")
async def build_preview(topic_id: str, body: ApproveRequest):
    """Compile the draft into the chosen format so the user reviews the real output before approving."""
    ws, run, content, template_file_path = await _load_for_compile(topic_id, body.content_markdown)
    preview_dir = OUTPUTS_DIR / topic_id / "preview"
    if preview_dir.exists():
        shutil.rmtree(preview_dir, ignore_errors=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    result = await _compile(topic_id, ws, content, template_file_path, preview_dir,
                            version=f"{len(run.get('deliverables') or []) + 1}.0")
    compiled = Path(result.file_path)
    base_url = f"/api/v1/workspaces/{topic_id}/preview-file"

    pdf = compiled if result.format == "PDF" else None
    if result.format in ("PPT", "DOCX"):
        pdf = await asyncio.to_thread(_convert_to_pdf, compiled)

    renderer = "pdf" if pdf else {"PPT": "pptx", "DOCX": "docx", "MD": "markdown"}.get(result.format, "markdown")
    return {
        "format": result.format,
        "renderer": renderer,
        "file_name": result.file_name,
        "file_url": f"{base_url}?file={compiled.name}",
        "pdf_url": f"{base_url}?file={pdf.name}" if pdf else None,
        "page_or_slide_count": _slide_count(result),
        "notes_count": _notes_count(result),
        "content_markdown": content,
        "built_at": _now(),
    }


@router.get("/{topic_id}/preview-file")
async def preview_file(topic_id: str, file: str):
    target = OUTPUTS_DIR / topic_id / "preview" / os.path.basename(file)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Preview not found. Build the preview again.")
    return FileResponse(
        target,
        media_type=FORMAT_MEDIA_TYPES.get(target.suffix.lower(), "application/octet-stream"),
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store"},
    )


# ─── Human-in-the-loop approval → final document ────────────────────────────────

@router.post("/{topic_id}/approve")
async def approve_and_compile(topic_id: str, body: ApproveRequest):
    ws, run, content, template_file_path = await _load_for_compile(topic_id, body.content_markdown)
    await _ws_update(topic_id, {"status": "COMPILING"})
    previous = run["deliverables"][-1] if run["deliverables"] else None
    version = f"{len(run['deliverables']) + 1}.0"
    try:
        result = await _compile(topic_id, ws, content, template_file_path, OUTPUTS_DIR / topic_id, version=version)
    except HTTPException:
        # Keep the reviewed draft so the user can fix it and approve again.
        await _ws_update(topic_id, {"status": "WAITING_FOR_REVIEW"})
        raise

    page_count = _slide_count(result)

    deliverable = {
        "file_name": result.file_name,
        "format": result.format,
        "file_size_bytes": result.file_size_bytes,
        "page_or_slide_count": page_count,
        "wcag_compliant": result.wcag_compliant,
        "accessibility_report": result.accessibility_report.model_dump() if result.accessibility_report else None,
        "download_url": f"/api/v1/workspaces/{topic_id}/export?file={result.file_name}",
        "compiled_at": _now(),
        "version": version,
        "change_note": _change_note(run, previous, content),
    }
    run["approved_content"] = content
    run["deliverables"] = [d for d in run["deliverables"] if d["file_name"] != result.file_name] + [deliverable]
    run["events"].append({
        "topic_id": topic_id,
        "agent_name": "Format Generation Agent",
        "status": "COMPLETED",
        "progress_percent": 100,
        "message": f"Compiled {result.file_name} — accessibility checks {'passed' if result.wcag_compliant else 'need attention'}.",
        "payload": deliverable,
        "timestamp": _now(),
    })
    await _ws_update(topic_id, {"status": "COMPLETED"})
    await _persist_run(topic_id)
    return deliverable


def _change_note(run: Dict[str, Any], previous: Optional[Dict[str, Any]], content: str) -> str:
    """What changed since the previous approved version, in plain words."""
    if previous is None:
        return "First approved version"
    since = previous.get("compiled_at", "")
    revisions = [r["instruction"] for r in run.get("revisions", []) if r.get("at", "") > since]
    if revisions:
        return "AI revisions: " + "; ".join(revisions[-3:])
    if content != run.get("approved_content"):
        return "Manual edits to the content"
    return "Recompiled without content changes"


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


@router.get("/{topic_id}/deliverable/preview")
async def get_deliverable_preview(topic_id: str):
    """
    Returns structured preview data for the compiled deliverable (.pptx, .docx, etc.)
    so the UI can render high-fidelity, native document views.
    """
    import re
    topic_dir = OUTPUTS_DIR / topic_id
    if not topic_dir.is_dir():
        return {"success": False, "detail": "No deliverables generated yet"}

    files = sorted((f for f in topic_dir.iterdir() if f.is_file()), key=lambda f: f.stat().st_mtime)
    if not files:
        return {"success": False, "detail": "No files found"}

    target = files[-1]
    ext = target.suffix.lower()

    if ext == ".pptx":
        try:
            import pptx
            prs = pptx.Presentation(str(target))
            slides = []
            for idx, slide in enumerate(prs.slides):
                is_cover = (idx == 0)
                s_data = {
                    "slide_number": idx + 1,
                    "is_cover": is_cover,
                    "title": "",
                    "subtitle": "",
                    "pill_badge": "",
                    "metadata": "",
                    "cards": [],
                    "stat_cards": [],
                    "table": None,
                    "footer_left": "",
                    "footer_right": "",
                }
                for shape in slide.shapes:
                    if shape.has_table:
                        tbl = shape.table
                        headers = [c.text.strip() for c in tbl.rows[0].cells]
                        rows = [[c.text.strip() for c in r.cells] for r in tbl.rows[1:]]
                        s_data["table"] = {"headers": headers, "rows": rows}
                    elif shape.has_text_frame:
                        txt = shape.text_frame.text.strip()
                        if not txt:
                            continue
                        if is_cover:
                            if "AGENT-101" in txt and ("SYSTEM DELIVERABLE" in txt or len(txt) < 40):
                                s_data["pill_badge"] = txt
                            elif not s_data["title"] and ("Outline" in txt or "Presentation" in txt or len(txt) < 100):
                                s_data["title"] = txt
                            elif "Autonomous" in txt or "Strict Topic" in txt:
                                s_data["subtitle"] = txt
                            elif "VERSION" in txt or "AUTHOR" in txt:
                                s_data["metadata"] = txt
                            elif not s_data["title"]:
                                s_data["title"] = txt
                        else:
                            if ("SLIDE " in txt and len(txt) <= 10) or txt == "SLIDE":
                                s_data["footer_right"] = txt
                            elif "AGENT-101" in txt and len(txt) < 80:
                                s_data["footer_left"] = txt
                            elif not s_data["title"] and len(txt) < 80 and "\n" not in txt:
                                s_data["title"] = txt
                            else:
                                paras = [p.text.strip() for p in shape.text_frame.paragraphs if p.text.strip()]
                                if len(paras) >= 2 and any(re.search(r"^\d", p) for p in paras[1:]):
                                    s_data["stat_cards"].append({
                                        "title": paras[0],
                                        "number": paras[1],
                                        "desc": paras[2] if len(paras) > 2 else ""
                                    })
                                else:
                                    s_data["cards"].append(txt)

                # Fallback for cover title if missed
                if is_cover and not s_data["title"]:
                    for shape in slide.shapes:
                        if shape.has_text_frame and shape.text_frame.text.strip():
                            t = shape.text_frame.text.strip()
                            if t != s_data["pill_badge"] and t != s_data["metadata"]:
                                s_data["title"] = t
                                break

                slides.append(s_data)

            templates = await _tpl_list(topic_id)
            template_guidance = templates[-1].get("guidance") if templates else None

            return {
                "success": True,
                "format": "PPT",
                "file_name": target.name,
                "file_size_bytes": target.stat().st_size,
                "slide_count": len(slides),
                "slides": slides,
                "template_guidance": template_guidance,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(str(target))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            tables = []
            for t in doc.tables:
                rows = [[c.text.strip() for c in r.cells] for r in t.rows]
                if rows:
                    tables.append({"headers": rows[0], "rows": rows[1:]})
            return {
                "success": True,
                "format": "DOCX",
                "file_name": target.name,
                "file_size_bytes": target.stat().st_size,
                "paragraphs": paragraphs,
                "tables": tables,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": True, "format": ext.lstrip(".").upper(), "file_name": target.name}


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
