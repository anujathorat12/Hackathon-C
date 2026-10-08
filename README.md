# AGENT-101 — Agentic Content Studio

> **Multi-Agent Content Generation System — Hackathon Project**
> From a one-line brief to a native, brand-styled, WCAG 2.2 AA–audited PPTX / DOCX / PDF / Markdown deliverable.

## 🔄 End-to-end flow

```
  Web Studio (React)  ──REST──▶  FastAPI gateway  ──▶  Agent pipeline (streamed live over WebSocket)
   · topic workspaces                                   1 Requirement Analysis
   · template upload                                    2 Planning
   · live telemetry                                     3 Reference Analysis  ◀── template parsers (DOCX · PPTX · PDF)
                                                        4 Research & Enrichment
                                                        5 Content Generation
                                                        6 Content Review  ──▶ waits for human review
   Human review (preview / edit) ──approve──▶           7 Format Generation ──▶ DOCX · PPTX · PDF · MD + WCAG 2.2 AA audit
   Download  ◀──────────────────────────────────────────  per-topic deliverable
```

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/login` · `register` | Authentication with PBKDF2 password hashing & session tokens |
| `GET /api/v1/auth/me` · `logout` | Active user profile & session invalidation |
| `GET /api/v1/auth/users` | Admin-only user directory listing |
| `POST /api/v1/auth/admin/users` | Admin user provisioning |
| `PATCH /api/v1/auth/admin/users/{id}/role` | Admin role promotion / demotion with self-demotion safety guard |
| `POST /api/v1/auth/admin/users/{id}/reset-password` | Admin password reset |
| `GET /api/v1/auth/admin/analytics` | Account health, token usage per request, latency & cost telemetry |
| `POST /api/v1/workspaces` · `GET` · `DELETE /{id}` | Topic workspaces (isolated context per topic) |
| `POST /api/v1/workspaces/{id}/templates` | Upload a reference template → extracts palette, fonts, layout |
| `WS /api/v1/workspaces/{id}/stream` | Runs agents 1–6, streams `RUNNING` / `COMPLETED` / `WAITING_FOR_REVIEW` events |
| `GET /api/v1/workspaces/{id}/run` | Snapshot of a run (events, refined content, deliverables) |
| `POST /api/v1/workspaces/{id}/approve` | Human approval (optionally with edited markdown) → Agent 7 compiles |
| `GET /api/v1/workspaces/{id}/export?file=` | Download this topic's deliverable |
| `GET /api/health` | API status, active LLM provider, backup chain & storage mode |

## 🔑 Demo Accounts (Pre-configured)

The system includes pre-seeded accounts for immediate review:

| Role | Email | Password | Access Privileges |
|---|---|---|---|
| **System Admin** | `admin@agent101.ai` | `admin123` | Full studio access + Admin Console (telemetry, token costs, user management) |
| **Studio Creator** | `user@agent101.ai` | `user123` | Topic workspaces, template ingestion, pipeline runs, deliverables |

> **Note:** Public registration automatically provisions `user` role. Public admin registration is strictly blocked by RBAC security policies.

## 🚀 Run the demo

```bash
# 1. Backend deps (once)
python -m venv venv
venv\Scripts\activate                 # Windows (or source venv/bin/activate on Unix)
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

Open **http://localhost:8000**. FastAPI serves the built UI, the REST API, and WebSocket channels.

**UI development with hot reload:** keep the backend running, then `cd frontend && npm run dev` and open http://localhost:5173 (`/api` is proxied to :8000).

### Configuration (`backend/.env`, see `.env.example`)

| Variable | Effect |
|---|---|
| `LLM_PROVIDER_CHAIN` | Comma-separated priority list (default: `groq,openrouter,mistral,gemini`). Auto-fails over in order upon rate-limits or downtime. |
| `GROQ_API_KEY` | Primary ultra-fast LLM provider (`openai/gpt-oss-120b`). |
| `OPENROUTER_API_KEY` | Secondary backup provider (`meta-llama/llama-3.3-70b-instruct`). |
| `MISTRAL_API_KEY` | Tertiary backup provider (`mistral-small-latest`). |
| `GEMINI_API_KEY` | OpenAI-compatible Google Gemini provider (`gemini-3.5-flash-lite`). |
| `MONGODB_URI` | Persists workspaces & user records. If MongoDB is unreachable, the API automatically uses an in-memory store (the header shows which). |

> **Zero-Key Deterministic Fallback:** If no API keys are provided or all providers experience outages, agents seamlessly switch to the deterministic offline cognitive engine.

## 🧪 Tests

```bash
python -m pytest tests -q                  # Auth, RBAC, agent unit tests + end-to-end API integration tests
python tests/test_document_compilers.py    # Document compiler test harness (DOCX, PPTX, PDF, MD)
```

## 📁 Layout

```
backend/app/
├── main.py                      # FastAPI app, serves frontend/dist
├── config.py                    # Multi-provider LLM chain & database configuration
├── api/
│   ├── auth.py                  # RBAC authentication, user management & admin telemetry
│   └── workspaces.py            # API: workspaces, upload, stream, approve, export
├── orchestration/               # Pipeline graph + async runner + cross-agent context memory
├── agents/cognitive/            # Agents 1 (reqs), 2 (plan), 4 (research), 5 (generate), 6 (review)
├── agents/document/             # Agent 3 (reference), agent 7 (format), WCAG 2.2 validator
├── parsers/ · converters/       # Template inspection + native DOCX/PPTX/PDF/MD builders
├── services/                    # LLM Multi-Provider Failover + Token Analytics + Vector Store
└── shared/schemas/              # Pydantic contracts
frontend/src/
├── components/
│   ├── LandingPage.jsx          # Public showcase & interactive workflow walk-through
│   ├── AuthModal.jsx            # Sign-in / registration with 1-click demo login
│   ├── AdminModal.jsx           # Token analytics, cost tracking, system health & user management
│   ├── Header.jsx               # Navigation bar with live provider failover telemetry & user pill
│   └── Workspace.jsx            # Multi-agent live telemetry, markdown editor & deliverable exports
tests/                           # Complete test suite (pytest + compiler harness)
```
