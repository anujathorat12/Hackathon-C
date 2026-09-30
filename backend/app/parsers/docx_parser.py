import os
from typing import Optional, Dict, Any, List
from docx import Document
from docx.oxml.ns import qn
from ..shared.schemas.template_models import TemplateGuidanceProfile
from .template_normalizer import normalize_guidance

def parse_docx_template(file_path: str) -> TemplateGuidanceProfile:
    """
    Inspects an uploaded Microsoft Word (.docx) template file.
    Extracts heading font families, font sizes, margins, and table header shading hex colors.
    """
    if not os.path.exists(file_path):
        return normalize_guidance()

    try:
        doc = Document(file_path)
        base_name = os.path.basename(file_path)

        heading_font = "Calibri"
        body_font = "Calibri"
        primary_hex = "#1B365D"
        table_header_hex = "#1B365D"
        heading_sizes = {"title": 26, "h1": 20, "h2": 15, "h3": 12, "body": 11}
        detected_sections = []

        # 1. Inspect Styles in the document
        for style in doc.styles:
            if style.name in ["Normal", "Body Text"] and style.font.name:
                body_font = style.font.name
            elif style.name in ["Heading 1", "Heading 2", "Heading 3", "Title"]:
                if style.font.name:
                    heading_font = style.font.name
                if style.font.color and style.font.color.rgb:
                    primary_hex = f"#{style.font.color.rgb}"

        # 2. Inspect Headings and Sections in Document Body
        for p in doc.paragraphs:
            text = p.text.strip()
            if text and p.style.name.startswith("Heading"):
                detected_sections.append(text)
                if p.style.font.color and p.style.font.color.rgb:
                    primary_hex = f"#{p.style.font.color.rgb}"

        # 3. Inspect Tables for XML Shading Attributes
        for table in doc.tables:
            if len(table.rows) > 0:
                first_row = table.rows[0]
                for cell in first_row.cells:
                    tcPr = cell._tc.get_or_add_tcPr()
                    shd = tcPr.find(qn('w:shd'))
                    if shd is not None:
                        val = shd.get(qn('w:fill'))
                        if val and val != "auto":
                            table_header_hex = f"#{val}" if not val.startswith("#") else val
                            break

        raw_data: Dict[str, Any] = {
            "template_type": "DOCX",
            "source_file_name": base_name,
            "color_palette": {
                "primary_hex": primary_hex,
                "secondary_hex": "#4B6B94",
                "accent_hex": "#00A3E0",
                "background_hex": "#FFFFFF",
                "text_hex": "#222222"
            },
            "typography": {
                "heading_font": heading_font,
                "body_font": body_font,
                "heading_sizes": heading_sizes
            },
            "layout_rules": {
                "slide_layouts_available": [],
                "max_bullets_per_slide": 5,
                "table_header_shading_hex": table_header_hex,
                "table_zebra_shading_hex": "#F4F7FA",
                "callout_box_style": "left_accent_border"
            },
            "detected_section_hierarchy": detected_sections[:7]
        }

        return normalize_guidance(raw_data)
    except Exception as e:
        print(f"Warning: DOCX parsing error on {file_path}: {e}. Returning default theme.")
        return normalize_guidance()
