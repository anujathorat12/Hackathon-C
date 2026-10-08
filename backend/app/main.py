import traceback
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.api.workspaces import router as workspaces_router
from app.api.auth import router as auth_router

app = FastAPI(
    title="AGENT-101 | Agentic Flow API",
    description="Multi-Agent Content Generation System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    # Return the real cause as JSON so the UI can show it instead of a bare "Internal Server Error".
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": f"Server error — {type(exc).__name__}: {exc}"})

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workspaces_router, prefix="/api/v1/workspaces", tags=["workspaces"])

from app.services.llm_service import llm_service

@app.get("/api/health")
def health_check():
    status = llm_service.get_provider_status()
    active_name = status.get("last_used_provider") or status.get("primary_provider") or "offline-fallback"
    active_obj = llm_service.providers.get(active_name)
    backups_count = max(0, len(llm_service.provider_chain) - 1)
    
    if active_obj:
        llm_label = f"{active_obj.display_name} ({backups_count} backups)" if backups_count > 0 else active_obj.display_name
    elif active_name != "offline-fallback":
        llm_label = f"{active_name} ({backups_count} backups)"
    else:
        llm_label = "offline-fallback"

    return {
        "status": "healthy",
        "version": "1.0.0",
        "storage": "mongodb" if get_database() is not None else "in-memory",
        "llm": llm_label,
        "active_provider": active_name,
        "backups_count": backups_count,
        "configured_providers": status["configured_providers"],
        "provider_chain": status["provider_chain"],
    }

# Serve the built React app (frontend/dist) when present — single-port demo mode.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
