import os
import re
from typing import List, Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

from ...shared.schemas.template_models import DocumentControlMetadata, TemplateGuidanceProfile
from .document_control import insert_document_control_page, hex_to_rgb
from ...shared.i18n import labels
from .table_styler import insert_styled_table

INLINE_MD = re.compile(r"(\*\*\*(?!\s).+?(?<!\s)\*\*\*|\*\*(?!\s).+?(?<!\s)\*\*|\*(?!\s)[^*]+?(?<!\s)\*)")


def add_markdown_runs(paragraph, text: str, font_name: str, size_pt: float, color: RGBColor, bold_color: RGBColor):
    """Add text as runs honouring ***bold italic***, **bold** and *italic* (underscores are left alone so
    file names in citations such as [Wellness_Policy.docx, §1] are not mangled)."""
    for part in INLINE_MD.split(text):
        if not part:
            continue
        bold = italic = False
        if part.startswith("***") and part.endswith("***") and len(part) > 6:
            part, bold, italic = part[3:-3], True, True
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            part, bold = part[2:-2], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            part, italic = part[1:-1], True
        run = paragraph.add_run(part)
        run.font.bold = bold or None
        run.font.italic = italic or None
        run.font.color.rgb = bold_color if bold else color
        run.font.name = font_name
        run.font.size = Pt(size_pt)


def _has_content(part) -> bool:
    """True if a header/footer has text or graphics (a logo) worth keeping."""
    xml = part._element.xml
    return bool(part.is_linked_to_previous is False and ("<w:drawing" in xml or "<w:pict" in xml or any(p.text.strip() for p in part.paragraphs)))


def build_docx_deliverable(
    markdown_content: str,
    output_path: str,
    metadata: Optional[DocumentControlMetadata] = None,
    guidance: Optional[TemplateGuidanceProfile] = None
) -> str:
    """
    Compiles refined markdown text into an executive-grade Microsoft Word (.docx) file.
    Includes:
      - Page 1 Document Control Audit Table with Cover Styling
      - Different First Page Header & Running Headers on Pages 2+
      - Running Footers with Classification & System ID
      - Accessible Heading Hierarchies (H1, H2, H3) with generous breathing space
      - Executive Callout Quote Boxes with Left Accent Borders
      - Native WCAG 2.2 AA Accessible Tables with Header Shading & Zebra Striping
    """
    if metadata is None:
        metadata = DocumentControlMetadata()
    if guidance is None:
        from ...parsers.template_normalizer import DEFAULT_CORPORATE_THEME
        guidance = DEFAULT_CORPORATE_THEME

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Brand-faithful path: write into the uploaded Word template so its styles, page setup,
    # header and footer (e.g. the company logo) are kept.
    template_path = guidance.source_file_path
    use_template = bool(template_path and template_path.lower().endswith(".docx") and os.path.exists(template_path))
    doc = Document(template_path) if use_template else Document()
    if use_template:
        body = doc.element.body
        for child in list(body):
            if child.tag != qn("w:sectPr"):
                body.remove(child)

    # Set standard 1-inch margins
    sections = doc.sections
    for section in sections:
        if use_template and (_has_content(section.header) or _has_content(section.footer)):
            continue  # keep the template's own margins, header and footer
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

        # Configure Header & Footer: Page 1 has no header, Pages 2+ have running header/footer
        section.different_first_page_header_footer = True

        # Running Header (Pages 2+)
        hdr = section.header
        hdr_p = hdr.paragraphs[0]
        hdr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hdr_run = hdr_p.add_run(metadata.document_title)
        hdr_run.font.name = guidance.typography.body_font
        hdr_run.font.size = Pt(8.5)
        hdr_run.font.color.rgb = RGBColor(140, 150, 160)

        # Running Footer (Pages 2+)
        ftr = section.footer
        ftr_p = ftr.paragraphs[0]
        ftr_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        L = labels(metadata.language)
        ftr_run1 = ftr_p.add_run(f"{L['version']} {metadata.version}  •  {metadata.date}  •  {L['prepared']}")
        ftr_run1.font.name = guidance.typography.body_font
        ftr_run1.font.size = Pt(8)
        ftr_run1.font.color.rgb = RGBColor(150, 160, 170)

    # 1. Page 1: Mandatory Document Control Table
    insert_document_control_page(doc, metadata, guidance)

    # 2. Parse Markdown Lines into Docx Elements
    lines = markdown_content.split('\n')
    line_idx = 0
    total_lines = len(lines)

    primary_rgb = hex_to_rgb(guidance.color_palette.primary_hex)
    secondary_rgb = hex_to_rgb(guidance.color_palette.secondary_hex)
    accent_rgb = hex_to_rgb(guidance.color_palette.accent_hex)
    accent_hex = guidance.color_palette.accent_hex.lstrip('#')

    while line_idx < total_lines:
        line = lines[line_idx].strip()

        # Skip slide separator tokens if present in markdown
        if line.startswith("<!-- slide -->") or line == "---":
            line_idx += 1
            continue

        # Skip empty lines
        if not line:
            line_idx += 1
            continue

        # Table detection: line starts and ends with '|'
        if line.startswith('|') and line.endswith('|'):
            table_lines: List[str] = []
            while line_idx < total_lines and lines[line_idx].strip().startswith('|') and lines[line_idx].strip().endswith('|'):
                table_lines.append(lines[line_idx].strip())
                line_idx += 1

            # Process table
            if len(table_lines) >= 2:
                hdr_cols = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                data_rows: List[List[str]] = []
                start_row = 2 if re.match(r'^[\|\s\:\-]+$', table_lines[1]) else 1

                for t_row in table_lines[start_row:]:
                    cols = [c.strip() for c in t_row.split('|')[1:-1]]
                    data_rows.append(cols)

                insert_styled_table(doc, hdr_cols, data_rows, guidance)
            continue

        # Heading 1: "# Title"
        if line.startswith('# '):
            text = line[2:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(22)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(text)
            run.font.name = guidance.typography.heading_font
            run.font.size = Pt(guidance.typography.heading_sizes.get("h1", 20))
            run.font.bold = True
            run.font.color.rgb = primary_rgb
            line_idx += 1
            continue

        # Heading 2: "## Section"
        if line.startswith('## '):
            text = line[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(text)
            run.font.name = guidance.typography.heading_font
            run.font.size = Pt(guidance.typography.heading_sizes.get("h2", 15))
            run.font.bold = True
            run.font.color.rgb = secondary_rgb
            line_idx += 1
            continue

        # Heading 3: "### Subsection"
        if line.startswith('### '):
            text = line[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(text)
            run.font.name = guidance.typography.heading_font
            run.font.size = Pt(guidance.typography.heading_sizes.get("h3", 12))
            run.font.bold = True
            run.font.color.rgb = secondary_rgb
            line_idx += 1
            continue

        # Blockquote / Executive Callout Box: "> text"
        if line.startswith('>'):
            callout_text = line.lstrip('> ').strip()
            # Render as single-cell table with left accent border
            c_table = doc.add_table(rows=1, cols=1)
            c_table.autofit = True
            cell = c_table.rows[0].cells[0]
            
            # Left accent border (3pt thick) & soft modern fill (#F8FAFC)
            tcPr = cell._tc.get_or_add_tcPr()
            border_xml = f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="{accent_hex}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>'
            tcPr.append(parse_xml(border_xml))
            shd_xml = f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>'
            tcPr.append(parse_xml(shd_xml))

            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.left_indent = Inches(0.12)
            p.paragraph_format.right_indent = Inches(0.12)
            
            add_markdown_runs(p, callout_text, guidance.typography.body_font, 10, RGBColor(55, 65, 81), primary_rgb)

            # Spacing after callout box
            post_p = doc.add_paragraph()
            post_p.paragraph_format.space_before = Pt(4)
            post_p.paragraph_format.space_after = Pt(4)

            line_idx += 1
            continue

        # Bullet List Items: "* item" or "- item"
        if line.startswith('* ') or line.startswith('- '):
            item_text = line[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(2.5)
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.line_spacing = 1.15
            
            add_markdown_runs(p, item_text, guidance.typography.body_font, 10.5, RGBColor(34, 34, 34), primary_rgb)
            line_idx += 1
            continue

        # Standard Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(7)
        p.paragraph_format.line_spacing = 1.18

        add_markdown_runs(p, line, guidance.typography.body_font, 10.5, RGBColor(34, 34, 34), primary_rgb)

        line_idx += 1

    doc.save(output_path)
    print(f"[DOCX Builder] Successfully generated executive deliverable: {output_path}")
    return output_path
