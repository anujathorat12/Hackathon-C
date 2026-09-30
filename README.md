# AGENT-101 — Module C: Document Compilers & Accessibility Engine

> **Multi-Agent Content Generation System — Hackathon Project**

## 🏗️ Architecture

Module C provides the **Document Compilation Pipeline** — responsible for analyzing reference templates, generating multi-format deliverables (DOCX, PPTX, PDF, Markdown), and enforcing WCAG 2.2 AA accessibility compliance.

```
backend/app/
├── agents/document/        # Agent orchestration layer
│   ├── reference_agent.py  # Agent 3 — Reference Template Analyzer
│   ├── format_agent.py     # Agent 7 — Multi-Format Compiler
│   └── wcag_validator.py   # WCAG 2.2 AA Accessibility Auditor
├── parsers/                # Template inspection engines
│   ├── docx_parser.py      # DOCX structure extractor
│   ├── pptx_parser.py      # PPTX layout analyzer
│   ├── pdf_parser.py       # PDF metadata parser
│   └── template_normalizer.py  # Unified schema normalizer
├── converters/             # Native format builders
│   ├── docx/               # Enterprise DOCX generator
│   │   ├── docx_builder.py
│   │   ├── document_control.py
│   │   └── table_styler.py
│   ├── pptx/               # Widescreen PPTX with dark theme
│   │   ├── pptx_builder.py
│   │   └── theme_styler.py
│   └── pdf_md/             # PDF & Markdown renderers
│       ├── pdf_builder.py
│       └── md_builder.py
└── shared/schemas/
    └── template_models.py  # Pydantic data contracts
```

## ✨ Key Features

- **Reference Template Analysis** — Extracts styles, hierarchies, and metadata from DOCX/PPTX/PDF templates
- **Multi-Format Generation** — Produces native PPTX (16:9, dark theme, KPI cards), DOCX (document control pages, accessible tables), PDF, and Markdown
- **WCAG 2.2 AA Compliance** — Automated auditing for color contrast (≥4.5:1), heading order, and screen-reader accessibility (`w:tblHeader` tagging)
- **Enterprise Styling** — Custom dark themes, gradient KPI stat cards, branded color palettes

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Schemas | Pydantic v2 |
| DOCX | python-docx + lxml |
| PPTX | python-pptx |
| PDF | xhtml2pdf |
| Database | MongoDB Atlas (shared) |

## 🚀 Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows

# Install dependencies
pip install python-docx python-pptx xhtml2pdf pydantic pymongo lxml
```

## 🧪 Testing

```bash
python -m pytest tests/test_document_compilers.py -v
```

## 👥 Team

| Member | Module | Responsibility |
|--------|--------|---------------|
| Siddharth (A) | UI & API Gateway | Frontend + FastAPI routing |
| Diya (B) | Agent Orchestration | LangGraph multi-agent pipeline |
| Anuja (C) | Document Compilers | This module — format generation & accessibility |

---
*Built for AGENT-101 Hackathon*
