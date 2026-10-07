"""
Turns uploaded source documents into citable passages for the research agent.

Each passage carries a human-checkable label — "report.pdf, p.3" for PDFs, "notes.docx, §2" for
Word/text files — which is exactly what the generated document cites.
"""
import os
import re
from typing import Dict, List

SUPPORTED_SOURCE_TYPES = {".pdf", ".docx", ".txt", ".md"}
PASSAGE_WORDS = 140


def _chunks(text: str, size: int = PASSAGE_WORDS) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


def _pages(path: str) -> List[tuple]:
    """(location label, text) units: PDF pages, or ~400-word blocks for Word/text."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return [(f"p.{n}", page.extract_text() or "") for n, page in enumerate(pdf.pages, 1)]
    if ext == ".docx":
        from docx import Document
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                text += "\n" + " | ".join(c.text.strip() for c in row.cells)
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    # Paragraph-sized sections keep "§n" citations specific enough to check by eye.
    blocks, current = [], ""
    for para in [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]:
        if current and len((current + " " + para).split()) > 120:
            blocks.append(current)
            current = para
        else:
            current = f"{current} {para}".strip()
    if current:
        blocks.append(current)
    return [(f"§{n}", block) for n, block in enumerate(blocks, 1)]


def extract_passages(path: str, display_name: str) -> List[Dict[str, str]]:
    """Passages ready for VectorService.seed_topic_knowledge."""
    passages = []
    for location, text in _pages(path):
        for chunk in _chunks(re.sub(r"\s+", " ", text)):
            if len(chunk.split()) >= 8:
                label = f"{display_name}, {location}"
                passages.append({"title": label, "label": label, "content": chunk, "source": display_name})
    return passages
