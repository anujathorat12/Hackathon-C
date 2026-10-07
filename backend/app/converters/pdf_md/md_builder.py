import os
from typing import Optional
from ...shared.schemas.template_models import DocumentControlMetadata

def build_md_deliverable(
    markdown_content: str,
    output_path: str,
    metadata: Optional[DocumentControlMetadata] = None
) -> str:
    """
    Exports a clean, publication-ready GitHub-flavored Markdown file,
    prepending an audit metadata header.
    """
    if metadata is None:
        metadata = DocumentControlMetadata()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    header = f"""---
title: "{metadata.document_title}"
deliverable_id: "{metadata.file_name}"
version: "{metadata.version}"
date: "{metadata.date}"
prepared_by: "{metadata.author}"
---

"""
    full_content = header + markdown_content.strip() + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"[MD Builder] Successfully exported Markdown: {output_path}")
    return output_path
