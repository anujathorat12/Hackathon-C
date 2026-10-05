# AGENT-101 — Agentic Content Studio

> **Multi-Agent Content Generation System — Hackathon Project**
> Modules A + B + C integrated: from a one-line brief to a native, brand-styled, WCAG 2.2 AA–audited PPTX / DOCX / PDF / Markdown deliverable.

## 🔄 End-to-end flow

```
 ┌──────────── Module A ────────────┐   ┌──────────────── Module B ─────────────────┐   ┌──────── Module C ────────┐
  React Studio  ──REST──▶  FastAPI     ──▶  1 Requirement Analysis                       
  (workspaces,             gateway          2 Planning                                    
   template upload)          │              3 Reference Analysis  ◀── Module C agent ───  parsers/ (docx·pptx·pdf)
        ▲                    │              4 Research & Enrichment                       
        │   WebSocket  ◀─────┘ live events  5 Content Generation                          
        │   telemetry                       6 Content Review  ──▶ WAITING_FOR_REVIEW      
        │                                                                                 
   Human review (preview / edit markdown) ──POST /approve──▶  7 Format Generation ──▶ converters/ + WCAG audit
        ▲                                                                                       │
        └──────────────────────────── GET /export (per-topic deliverable) ◀─────────────────────┘
```

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/workspaces` · `GET` · `DELETE /{id}` | Topic workspaces (isolated context per topic) |
| `POST /api/v1/workspaces/{id}/templates` | Upload a reference template → Module C extracts palette, fonts, layout |
| `WS /api/v1/workspaces/{id}/stream` | Runs agents 1–6, streams `RUNNING` / `COMPLETED` / `WAITING_FOR_REVIEW` events |
| `GET /api/v1/workspaces/{id}/run` | Snapshot of a run (events, refined content, deliverables) |
| `POST /api/v1/workspaces/{id}/approve` | Human approval (optionally with edited markdown) → Agent 7 compiles |
| `GET /api/v1/workspaces/{id}/export?file=` | Download this topic's deliverable |
| `GET /api/health` | API status, LLM mode, storage mode |

## 🚀 Run the demo

```bash
# 1. Backend deps (once)
python -m venv venv
venv\Scripts\activate                 # Windows
pip install -r requirements.txt

# 2. Frontend build (once, or after UI changes)
cd frontend
npm install
npm run build
cd ..

# 3. Start everything on one port
cd backend
uvicorn app.main:app --port 8000
```

Open **http://localhost:8000**. FastAPI serves the built UI, the REST API and the WebSocket.

**UI development with hot reload:** keep the backend running, then `cd frontend && npm run dev` and open http://localhost:5173 (`/api` is proxied to :8000).

### Configuration (`backend/.env`, see `.env.example`)

| Variable | Effect |
|---|---|
| `GROQ_API_KEY` | Enables live LLM generation. **Without it, agents use the deterministic offline fallback, so every topic produces the same sample content.** Set it for a topic-specific demo. |
| `MONGODB_URI` | Persists workspaces. If MongoDB is unreachable, the API automatically uses an in-memory store (the header shows which). |

## 🧪 Tests

```bash
python -m pytest tests -q                  # Module B unit tests + A→B→C API integration tests (all 4 formats)
python tests/test_document_compilers.py    # Module C standalone compiler harness
```

## 📁 Layout

```
backend/app/
├── main.py                      # FastAPI app, serves frontend/dist
├── api/workspaces.py            # Module A gateway: workspaces, upload, stream, approve, export
├── orchestration/               # Module B: pipeline graph + async runner
├── agents/cognitive/            # Module B: agents 1, 2, 4, 5, 6
├── agents/document/             # Module C: agent 3 (reference), agent 7 (format), WCAG validator
├── parsers/ · converters/       # Module C: template inspection + native DOCX/PPTX/PDF/MD builders
├── services/                    # LLM (Groq/OpenAI-compatible) + topic-scoped vector store
└── shared/schemas/              # Pydantic contracts
frontend/src/                    # Module A: React studio (Vite)
tests/                           # Unit + integration tests
```

## 👥 Team

| Member | Module | Responsibility |
|--------|--------|---------------|
| Siddharth (A) | UI & API Gateway | Frontend + FastAPI routing |
| Diya (B) | Agent Orchestration | Multi-agent cognitive pipeline |
| Anuja (C) | Document Compilers | Template analysis, format generation & accessibility |

---
*Built for AGENT-101 Hackathon*
