# ContentGenie — Agentic Content Studio

> **Multi-Agent Content Generation System — Hackathon Project**
> From a one-line brief (and, optionally, your own documents and brand template) to a native, brand-styled
> PowerPoint, Word, PDF or Markdown deliverable — reviewed and approved by a human before it is final.

## ✨ What it does

| Capability | Details |
|---|---|
| **7 collaborating agents** | Requirements → Planning → Reference (template) analysis → Research → Writing → Review → Format generation, streamed live |
| **Brand-perfect templates** | Upload a `.pptx` and the deck is built *inside* its own layouts (logo, footer, fonts, bullets, slide numbers). A `.docx` template keeps its header/footer. Brand colours are read from the template theme. |
| **Bring your own sources** | Upload PDFs, Word files or notes; agents write only from them and cite `[file, p.N]`. A source check verifies every citation and flags figures with no citation. |
| **Review the real file** | Before approving, preview the actual slides, Word pages or PDF — not a mock-up |
| **Ask AI to revise** | "Make slide 3 shorter", "add an Indian example": rewrites only the chosen slide/section, with undo |
| **Speaker notes** | Every generated slide gets presenter talking points |
| **Multilingual** | English, Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Kannada, Spanish, French, German |
| **Value meter** | Real time and AI cost per document, against a stated manual-effort baseline; running totals |
| **Version history** | Each approval is a new version (v1.0, v2.0…) with what changed; all versions downloadable |
| **Honest quality signals** | Measured reading grade, words trimmed, citations; automated accessibility checks (contrast, heading order, table headers) |
| **Restart-proof** | Topics, drafts, versions and totals persist in MongoDB Atlas |

## 🔄 End-to-end flow

```
  Web Studio (React)  ──REST──▶  FastAPI gateway  ──▶  Agent pipeline (streamed live over WebSocket)
   · topic + template + sources                         1 Requirement Analysis
   · language                                           2 Planning            ◀── digest of your sources
   · live telemetry                                     3 Reference Analysis  ◀── template theme + layouts
                                                        4 Research            ◀── passages from your sources
                                                        5 Content Generation
                                                        6 Content Review      ──▶ citation & source check
   Review: real-format preview · Ask AI · edit ──approve──▶ 7 Format Generation ──▶ PPTX · DOCX · PDF · MD
   Download any version  ◀─────────────────────────────────  + speaker notes · accessibility checks
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
| `POST /api/v1/workspaces/{id}/templates` | Upload a brand template → theme colours, fonts, layouts, slide structure |
| `POST /api/v1/workspaces/{id}/sources` · `GET` · `DELETE /{id}/sources/{sid}` | Source documents the agents write from |
| `WS /api/v1/workspaces/{id}/stream` | Runs agents 1–6 and streams progress |
| `POST /api/v1/workspaces/{id}/preview` | Compile the draft in the chosen format for review |
| `POST /api/v1/workspaces/{id}/revise` | Ask AI to revise the whole draft or one section |
| `POST /api/v1/workspaces/{id}/approve` | Approve → new version compiled |
| `GET /api/v1/workspaces/{id}/run` | Run snapshot (events, draft, versions) — restored after restarts |
| `GET /api/v1/workspaces/{id}/export?file=` | Download a version |
| `GET /api/v1/workspaces/{id}/deliverable/preview` | Structured slide/page data for the interactive preview |
| `GET /api/v1/workspaces/stats/summary` | Value-meter totals |
| `/api/v1/auth/*` | Sign-in, registration, users and admin telemetry (RBAC) |
| `GET /api/health` | API status, active LLM provider, backup chain & storage mode |

## 🔑 Demo Accounts (Pre-configured)

The system includes pre-seeded accounts for immediate review:

| Role | Email | Password | Access Privileges |
|---|---|---|---|
| **System Admin** | `admin@contentgenie.ai` | `admin123` | Full studio access + Admin Console (telemetry, token costs, user management) |
| **Studio Creator** | `user@contentgenie.ai` | `user123` | Topic workspaces, template ingestion, pipeline runs, deliverables |

> **Note:** Public registration automatically provisions `user` role. Public admin registration is strictly blocked by RBAC security policies.

## 🚀 Run locally

```bash
# 1. Backend deps (once)
python -m venv venv
venv\Scripts\activate                 # Windows  (source venv/bin/activate on Mac/Linux)
pip install -r requirements.txt

# 2. Frontend build (once, or after UI changes)
cd frontend
npm install
npm run build
cd ..

# 3. Configure, then start everything on one port
copy backend\.env.example backend\.env  # then edit it (see below)
cd backend
uvicorn app.main:app --port 8000
```

Open **http://localhost:8000**. FastAPI serves the built UI, the REST API and the WebSocket.
UI development with hot reload: keep the backend running, then `cd frontend && npm run dev` (http://localhost:5173).

### Configuration (`backend/.env` — never commit it)

| Variable | Effect |
|---|---|
| `LLM_PROVIDER_CHAIN` | Comma-separated priority list (default: `groq,openrouter,mistral,gemini`). Auto-fails over in order upon rate-limits or downtime. |
| `GROQ_API_KEY` | Primary ultra-fast LLM provider (`openai/gpt-oss-120b`). |
| `OPENROUTER_API_KEY` | Secondary backup provider (`meta-llama/llama-3.3-70b-instruct`). |
| `MISTRAL_API_KEY` | Tertiary backup provider (`mistral-small-latest`). |
| `GEMINI_API_KEY` | OpenAI-compatible Google Gemini provider (`gemini-3.5-flash-lite`). |
| `MONGODB_URI` | MongoDB Atlas connection string; persists workspaces & user records. Empty/unreachable → in-memory store. |
| `USD_TO_INR`, `MANUAL_WORDS_PER_HOUR`, `MANUAL_OVERHEAD_MINUTES` | Value-meter assumptions (defaults 88, 400, 60) |

> **Zero-Key Deterministic Fallback:** If no API keys are provided or all providers fail, agents switch to the offline engine and the UI shows a "sample content" warning.

## 🌐 Public link (for judges to try on their phones)

The repo ships a `Dockerfile` (builds the UI and serves everything on one port) and a `render.yaml` blueprint.

1. Push the repo to GitHub, then on [render.com](https://render.com): **New + → Blueprint** → select the repo.
2. Enter `GROQ_API_KEY` and `MONGODB_URI` when prompted (in MongoDB Atlas → Network Access, allow `0.0.0.0/0`).
3. Open the URL Render gives you and click **Share** in the header for a scannable QR code.

Or anywhere with Docker: `docker build -t contentgenie . && docker run -p 8000:8000 --env-file backend/.env contentgenie`.
On free hosting, uploaded files and generated documents are kept until the service restarts; topics and history live in Atlas.

## 🧪 Tests

```bash
python -m pytest tests -q                  # auth/RBAC, agents, end-to-end API: 4 formats, versions, restart recovery, sources, revise
python tests/test_document_compilers.py    # document compiler harness (DOCX, PPTX, PDF, MD)
```

Tests always run offline (no AI key, no database) — see `tests/conftest.py`.

## 📁 Layout

```
backend/app/
├── main.py                      # FastAPI app, serves frontend/dist
├── config.py                    # Multi-provider LLM chain & database configuration
├── api/
│   ├── auth.py                  # RBAC authentication, user management & admin telemetry
│   └── workspaces.py            # workspaces, templates, sources, stream, preview, revise, approve, export, stats
├── orchestration/               # pipeline graph + async runner (value meter, citation check, context memory)
├── agents/cognitive/            # requirement, planning, research, generation, review, revision, speaker notes
├── agents/document/             # reference analysis, format generation, accessibility checks
├── parsers/                     # template inspection + theme reader
├── converters/                  # native DOCX / PPTX (incl. build-inside-template) / PDF / MD builders
├── services/                    # multi-provider LLM failover, token analytics, passage store, source ingestion
└── shared/                      # Pydantic contracts + i18n labels
frontend/src/
├── components/
│   ├── LandingPage.jsx          # Public showcase & workflow walk-through
│   ├── AuthModal.jsx            # Sign-in / registration with 1-click demo login
│   ├── AdminModal.jsx           # Token analytics, cost tracking, system health & user management
│   ├── ReviewStudio.jsx         # Review: exact-file / interactive / outline previews, Ask AI, source check
│   ├── SlideDeckPreview.jsx · WordDocumentPreview.jsx  # Interactive in-browser previews
│   └── Workspace.jsx            # Live agent pipeline, telemetry, versions & deliverables
tests/                           # Unit + integration tests
Dockerfile · render.yaml          # Container + one-click hosting
```
