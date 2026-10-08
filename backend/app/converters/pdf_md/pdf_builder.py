import os
from typing import Optional
import markdown
from ...shared.schemas.template_models import DocumentControlMetadata, TemplateGuidanceProfile
from ...shared.i18n import labels

PDF_SAFE_CHARS = {
    "‐": "-", "‑": "-", "‒": "-", "−": "-",
    "→": "->", "←": "<-", "↔": "<->", "⇒": "=>",
    "≈": "~", "≤": "<=", "≥": ">=", " ": " ", " ": " ", "​": "",
}

def build_pdf_deliverable(
    markdown_content: str,
    output_path: str,
    metadata: Optional[DocumentControlMetadata] = None,
    guidance: Optional[TemplateGuidanceProfile] = None
) -> str:
    """
    Compiles refined markdown text into a styled, publication-ready PDF deliverable.
    Includes custom print CSS styles for margins, headers, and accessible tables.
    """
    if metadata is None:
        metadata = DocumentControlMetadata()
    if guidance is None:
        from ...parsers.template_normalizer import DEFAULT_CORPORATE_THEME
        guidance = DEFAULT_CORPORATE_THEME

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    L = labels(metadata.language)

    # The PDF's built-in fonts lack some Unicode punctuation LLMs use (non-breaking hyphens, arrows),
    # which would render as empty boxes; swap them for plain equivalents.
    for char, plain in PDF_SAFE_CHARS.items():
        markdown_content = markdown_content.replace(char, plain)

    # Convert markdown to HTML with table and fenced code extensions
    html_body = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )

    primary_hex = guidance.color_palette.primary_hex
    secondary_hex = guidance.color_palette.secondary_hex
    font_family = guidance.typography.heading_font
    zebra_hex = guidance.layout_rules.table_zebra_shading_hex

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>{metadata.document_title}</title>
<style>
  @page {{
    size: letter portrait;
    margin: 1in;
    @bottom-right {{
      content: "Page " counter(page);
      font-size: 9pt;
      color: #777777;
    }}
    @top-right {{
      content: "{metadata.file_name}";
      font-size: 8pt;
      color: #999999;
    }}
  }}
  body {{
    font-family: '{font_family}', Arial, sans-serif;
    color: #222222;
    line-height: 1.5;
    font-size: 11pt;
  }}
  h1 {{
    color: {primary_hex};
    font-size: 22pt;
    border-bottom: 2px solid {primary_hex};
    padding-bottom: 4px;
    margin-top: 20px;
  }}
  h2 {{
    color: {secondary_hex};
    font-size: 16pt;
    margin-top: 16px;
  }}
  h3 {{
    color: {secondary_hex};
    font-size: 13pt;
    margin-top: 12px;
  }}
  blockquote {{
    border-left: 4px solid {guidance.color_palette.accent_hex};
    background-color: #F8FAFC;
    margin: 12px 0;
    padding: 10px 14px;
    font-style: italic;
    color: #444444;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 10pt;
  }}
  th {{
    background-color: {primary_hex};
    color: #ffffff;
    font-weight: bold;
    padding: 8px 10px;
    text-align: left;
    border: 1px solid #cccccc;
  }}
  td {{
    padding: 7px 10px;
    border: 1px solid #dddddd;
  }}
  tr:nth-child(even) {{
    background-color: {zebra_hex};
  }}
  .document-control {{
    margin-bottom: 30px;
    border: 1px solid #1B365D;
  }}
  .document-control th {{
    background-color: {primary_hex};
  }}
</style>
</head>
<body>
  <div style="margin-bottom: 30px;">
    <h1 style="border: none; margin-bottom: 2px;">{metadata.document_title}</h1>
    <p style="color: {secondary_hex}; font-size: 10pt; font-weight: bold; margin-top: 0;">
      {L["version"].upper()} {metadata.version} • {metadata.date}
    </p>
  </div>

  <table class="document-control">
    <tr><th colspan="2">{L["document_control"]}</th></tr>
    <tr><td><strong>{L["document_title"]}</strong></td><td>{metadata.document_title}</td></tr>
    <tr><td><strong>{L["file_name"]}</strong></td><td>{metadata.file_name}</td></tr>
    <tr><td><strong>{L["version"]}</strong></td><td>{metadata.version}</td></tr>
    <tr><td><strong>{L["date"]}</strong></td><td>{metadata.date}</td></tr>
    <tr><td><strong>{L["authorship"]}</strong></td><td>{metadata.author}</td></tr>
    <tr><td><strong>{L["accessibility"]}</strong></td><td>{L["accessibility_text"]}</td></tr>
  </table>

  <div style="page-break-after: always;"></div>

  {html_body}
</body>
</html>
"""

    # Compile HTML to PDF using xhtml2pdf
    try:
        from xhtml2pdf import pisa
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
            if pisa_status.err:
                print(f"[PDF Builder] Warning: xhtml2pdf reported error code {pisa_status.err}")
        print(f"[PDF Builder] Successfully generated PDF deliverable: {output_path}")
        return output_path
    except Exception as e:
        print(f"[PDF Builder] Error compiling PDF: {e}")
        # Write HTML as fallback
        html_fallback = output_path.replace(".pdf", ".html")
        with open(html_fallback, "w", encoding="utf-8") as f:
            f.write(full_html)
        return html_fallback
