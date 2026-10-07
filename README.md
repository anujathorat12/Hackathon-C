# AGENT-101 — Agentic Content Studio

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
| `POST /api/v1/workspaces` · `GET` · `DELETE /{id}` | Topic workspaces (isolated context per topic) |
| `POST /api/v1/workspaces/{id}/templates` | Upload a brand template → theme colours, fonts, layouts |
| `POST /api/v1/workspaces/{id}/sources` · `GET` · `DELETE /{id}/sources/{sid}` | Source documents the agents write from |
| `WS /api/v1/workspaces/{id}/stream` | Runs agents 1–6 and streams progress |
| `POST /api/v1/workspaces/{id}/preview` | Compile the draft in the chosen format for review |
| `POST /api/v1/workspaces/{id}/revise` | Ask AI to revise the whole draft or one section |
| `POST /api/v1/workspaces/{id}/approve` | Approve → new version compiled |
| `GET /api/v1/workspaces/{id}/run` | Run snapshot (events, draft, versions) — restored after restarts |
| `GET /api/v1/workspaces/{id}/export?file=` | Download a version |
| `GET /api/v1/workspaces/stats/summary` | Value-meter totals |
| `GET /api/health` | API, LLM and storage status |

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
| `GROQ_API_KEY` | Live AI generation. Without it the agents use offline sample content (the UI warns when that happens). |
| `LLM_MODEL` | `openai/gpt-oss-120b` (Groq model id) |
| `MONGODB_URI` | MongoDB Atlas connection string. Empty/unreachable → in-memory store. |
| `USD_TO_INR`, `MANUAL_WORDS_PER_HOUR`, `MANUAL_OVERHEAD_MINUTES` | Value-meter assumptions (defaults 88, 400, 60) |

## 🌐 Public link (for judges to try on their phones)

The repo ships a `Dockerfile` (builds the UI and serves everything on one port) and a `render.yaml` blueprint.

1. Push the repo to GitHub, then on [render.com](https://render.com): **New + → Blueprint** → select the repo.
2. Enter `GROQ_API_KEY` and `MONGODB_URI` when prompted (in MongoDB Atlas → Network Access, allow `0.0.0.0/0`).
3. Open the URL Render gives you and click **Share** in the header for a scannable QR code.

Or anywhere with Docker: `docker build -t agent-101 . && docker run -p 8000:8000 --env-file backend/.env agent-101`.
On free hosting, uploaded files and generated documents are kept until the service restarts; topics and history live in Atlas.

## 🧪 Tests

```bash
python -m pytest tests -q                  # agents + end-to-end API: 4 formats, versions, restart recovery, sources, revise
python tests/test_document_compilers.py    # document compiler harness
```

Tests always run offline (no AI key, no database) — see `tests/conftest.py`.

## 📁 Layout

```
backend/app/
├── main.py                      # FastAPI app, serves frontend/dist
├── api/workspaces.py            # workspaces, templates, sources, stream, preview, revise, approve, export, stats
├── orchestration/               # pipeline graph + async runner (value meter, citation check)
├── agents/cognitive/            # requirement, planning, research, generation, review, revision, speaker notes
├── agents/document/             # reference analysis, format generation, accessibility checks
├── parsers/                     # template inspection + theme reader
├── converters/                  # native DOCX / PPTX (incl. build-inside-template) / PDF / MD builders
├── services/                    # LLM client, topic-scoped passage store, source ingestion
└── shared/schemas/              # Pydantic contracts
frontend/src/                    # React studio (Vite)
tests/                           # Unit + integration tests
Dockerfile · render.yaml          # Container + one-click hosting
```
