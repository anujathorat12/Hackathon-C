from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from ...shared.schemas.template_models import DocumentControlMetadata, TemplateGuidanceProfile
from ...shared.i18n import labels

def hex_to_rgb(hex_str: str) -> RGBColor:
    hex_clean = hex_str.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join([c*2 for c in hex_clean])
    return RGBColor(int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16))

def insert_document_control_page(
    doc: Document,
    metadata: DocumentControlMetadata,
    guidance: TemplateGuidanceProfile
):
    """
    Inserts a standardized Page 1 Document Control Table and cover title
    as mandated by the ContentGenie Style Guide.
    """
    primary_rgb = hex_to_rgb(guidance.color_palette.primary_hex)
    primary_hex = guidance.color_palette.primary_hex.lstrip('#')

    # 1. Main Document Cover Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(36)
    title_p.paragraph_format.space_after = Pt(12)
    title_run = title_p.add_run(metadata.document_title)
    title_run.font.name = guidance.typography.heading_font
    title_run.font.size = Pt(guidance.typography.heading_sizes.get("title", 26))
    title_run.font.bold = True
    title_run.font.color.rgb = primary_rgb

    # Subtitle / Classification Pill
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(32)
    L = labels(metadata.language)
    sub_run = sub_p.add_run(f"{L['version']} {metadata.version}  •  {metadata.date}".upper())
    sub_run.font.name = guidance.typography.body_font
    sub_run.font.size = Pt(10)
    sub_run.font.bold = True
    sub_run.font.color.rgb = hex_to_rgb(guidance.color_palette.secondary_hex)

    # 2. Document Control Table Header Label
    lbl_p = doc.add_paragraph()
    lbl_p.paragraph_format.space_after = Pt(6)
    lbl_run = lbl_p.add_run(L["document_control"])
    lbl_run.font.name = guidance.typography.heading_font
    lbl_run.font.size = Pt(13)
    lbl_run.font.bold = True
    lbl_run.font.color.rgb = primary_rgb

    # 3. Create the 2-Column Document Control Table
    table_rows = [
        (L["item"], L["detail"]),
        (L["document_title"], metadata.document_title),
        (L["file_name"], metadata.file_name),
        (L["version"], metadata.version),
        (L["date"], metadata.date),
        (L["authorship"], metadata.author),
        (L["accessibility"], L["accessibility_text"])
    ]

    table = doc.add_table(rows=len(table_rows), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Set column widths (Column 1: 2.2 inches, Column 2: 4.3 inches)
    col_widths = [Inches(2.2), Inches(4.3)]
    for row_idx, row_data in enumerate(table_rows):
        row = table.rows[row_idx]
        
        # Apply XML row height & header attributes
        trPr = row._tr.get_or_add_trPr()
        if row_idx == 0:
            # Tag header row for accessibility
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

        for col_idx, text in enumerate(row_data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            cell_p = cell.paragraphs[0]
            cell_p.paragraph_format.space_before = Pt(4)
            cell_p.paragraph_format.space_after = Pt(4)
            run = cell_p.add_run(text)
            run.font.name = guidance.typography.body_font
            run.font.size = Pt(10)

            # Cell shading
            if row_idx == 0:
                # Header row fill: Primary brand color with bold white text
                shading_xml = f'<w:shd {nsdecls("w")} w:fill="{primary_hex}"/>'
                cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
            elif row_idx % 2 == 1:
                # Zebra striping: Light subtle tint
                shd_hex = guidance.layout_rules.table_zebra_shading_hex.lstrip('#')
                shading_xml = f'<w:shd {nsdecls("w")} w:fill="{shd_hex}"/>'
                cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))
                if col_idx == 0:
                    run.font.bold = True
            else:
                if col_idx == 0:
                    run.font.bold = True

    # 4. Mandatory Page Break after Page 1 Document Control
    doc.add_page_break()
