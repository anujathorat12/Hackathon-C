from typing import List
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from ...shared.schemas.template_models import TemplateGuidanceProfile

def insert_styled_table(
    doc: Document,
    header_row: List[str],
    data_rows: List[List[str]],
    guidance: TemplateGuidanceProfile
):
    """
    Renders an elite, fully accessible native Word table from markdown table rows.
    Implements WCAG 2.2 AA standard:
      - w:tblHeader XML tag on row 0 (so screen readers repeat headers on multi-page tables)
      - Minimum 4.5:1 text-to-background contrast ratio (bold white text on brand primary fill)
      - Clean modern borders (subtle #D1D5DB) and zebra striping (#F8FAFC)
      - Generous cell padding for executive legibility
    """
    if not header_row:
        return

    num_cols = len(header_row)
    total_rows = 1 + len(data_rows)
    table = doc.add_table(rows=total_rows, cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    primary_hex = guidance.color_palette.primary_hex.lstrip('#')
    zebra_hex = guidance.layout_rules.table_zebra_shading_hex.lstrip('#')

    # Apply modern subtle table borders (#CBD5E1) via XML
    tblPr = table._tbl.tblPr
    borders_xml = f"""
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
        <w:bottom w:val="single" w:sz="8" w:space="0" w:color="{primary_hex}"/>
        <w:left w:val="none"/>
        <w:right w:val="none"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
        <w:insideV w:val="none"/>
    </w:tblBorders>
    """
    tblPr.append(parse_xml(borders_xml))

    # 1. Format Header Row
    hdr_row = table.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    # WCAG Mandatory tblHeader tag for screen readers
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

    for col_idx, col_title in enumerate(header_row):
        cell = hdr_row.cells[col_idx]
        cell_p = cell.paragraphs[0]
        cell_p.paragraph_format.space_before = Pt(6)
        cell_p.paragraph_format.space_after = Pt(6)
        cell_p.paragraph_format.left_indent = Inches(0.08)
        cell_p.paragraph_format.right_indent = Inches(0.08)
        
        run = cell_p.add_run(col_title.strip())
        run.font.name = guidance.typography.heading_font
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)  # High contrast white

        # Apply header background fill
        shd_xml = f'<w:shd {nsdecls("w")} w:fill="{primary_hex}"/>'
        cell._tc.get_or_add_tcPr().append(parse_xml(shd_xml))

    # 2. Format Data Rows
    for row_idx, row_values in enumerate(data_rows):
        table_row = table.rows[row_idx + 1]
        is_even = (row_idx % 2 == 1)

        for col_idx in range(num_cols):
            val = row_values[col_idx].strip() if col_idx < len(row_values) else ""
            cell = table_row.cells[col_idx]
            cell_p = cell.paragraphs[0]
            cell_p.paragraph_format.space_before = Pt(5)
            cell_p.paragraph_format.space_after = Pt(5)
            cell_p.paragraph_format.left_indent = Inches(0.08)
            cell_p.paragraph_format.right_indent = Inches(0.08)

            run = cell_p.add_run(val)
            run.font.name = guidance.typography.body_font
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(34, 34, 34)

            # Highlight first column if it represents category
            if col_idx == 0:
                run.font.bold = True

            # Zebra striping on alternating rows
            if is_even:
                shd_xml = f'<w:shd {nsdecls("w")} w:fill="{zebra_hex}"/>'
                cell._tc.get_or_add_tcPr().append(parse_xml(shd_xml))

    # Spacing after table
    post_p = doc.add_paragraph()
    post_p.paragraph_format.space_before = Pt(8)
    post_p.paragraph_format.space_after = Pt(6)
