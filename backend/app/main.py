import traceback
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.api.workspaces import router as workspaces_router

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

app.include_router(workspaces_router, prefix="/api/v1/workspaces", tags=["workspaces"])

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "storage": "mongodb" if get_database() is not None else "in-memory",
        "llm": settings.LLM_MODEL if settings.GROQ_API_KEY else "offline-fallback",
    }

# Serve the built React app (frontend/dist) when present — single-port demo mode.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
