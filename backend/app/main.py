from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.api.workspaces import router as workspaces_router

app = FastAPI(
    title="AGENT-101 | Agentic Flow API",
    description="Multi-Agent Content Generation System — Modules A + B + C Integrated",
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

app.include_router(workspaces_router, prefix="/api/v1/workspaces", tags=["workspaces"])

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "storage": "mongodb" if get_database() is not None else "in-memory",
        "llm": settings.LLM_MODEL if settings.GROQ_API_KEY else "offline-fallback",
        "modules": ["A: Gateway & Workspaces", "B: Cognitive Engine", "C: Document Compilers"],
    }

# Serve the built React app (frontend/dist) when present — single-port demo mode.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
