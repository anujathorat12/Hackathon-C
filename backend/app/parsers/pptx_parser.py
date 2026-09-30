import os
from typing import Optional, Dict, Any, List
from pptx import Presentation
from ..shared.schemas.template_models import TemplateGuidanceProfile
from .template_normalizer import normalize_guidance

def parse_pptx_template(file_path: str) -> TemplateGuidanceProfile:
    """
    Inspects an uploaded PowerPoint (.pptx) template file.
    Extracts available slide layouts, font families, and color theme hints.
    """
    if not os.path.exists(file_path):
        return normalize_guidance()

    try:
        prs = Presentation(file_path)
        base_name = os.path.basename(file_path)

        available_layouts: List[str] = []
        heading_font = "Calibri"
        primary_hex = "#1B365D"

        # 1. Inspect Slide Layouts in Slide Master
        for layout in prs.slide_layouts:
            name = layout.name.strip() if layout.name else "Custom Layout"
            if name not in available_layouts:
                available_layouts.append(name)

        # 2. Inspect Sample Shapes and Text Frames for Fonts and Colors
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if paragraph.font.name:
                            heading_font = paragraph.font.name
                        if paragraph.font.color and paragraph.font.color.rgb:
                            primary_hex = f"#{paragraph.font.color.rgb}"
                            break

        raw_data: Dict[str, Any] = {
            "template_type": "PPTX",
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
                "body_font": heading_font,
                "heading_sizes": {"title": 28, "h1": 22, "h2": 18, "h3": 14, "body": 12}
            },
            "layout_rules": {
                "slide_layouts_available": available_layouts if available_layouts else ["Title Slide", "Title and Content"],
                "max_bullets_per_slide": 5,
                "table_header_shading_hex": primary_hex,
                "table_zebra_shading_hex": "#F4F7FA",
                "callout_box_style": "left_accent_border"
            },
            "detected_section_hierarchy": []
        }

        return normalize_guidance(raw_data)
    except Exception as e:
        print(f"Warning: PPTX parsing error on {file_path}: {e}. Returning default theme.")
        return normalize_guidance()
