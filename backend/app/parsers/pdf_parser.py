import os
from typing import List, Dict, Any
import pdfplumber
from ..shared.schemas.template_models import TemplateGuidanceProfile
from .template_normalizer import normalize_guidance

def parse_pdf_template(file_path: str) -> TemplateGuidanceProfile:
    """
    Inspects an uploaded PDF document or academic research paper.
    Extracts structural section headings (e.g. Abstract, Introduction, Methodology, Results).
    """
    if not os.path.exists(file_path):
        return normalize_guidance()

    try:
        detected_sections: List[str] = []
        base_name = os.path.basename(file_path)

        standard_academic_headers = [
            "abstract", "introduction", "background", "literature review",
            "methodology", "methods", "system architecture", "experimental setup",
            "results", "discussion", "limitations", "conclusion", "references"
        ]

        with pdfplumber.open(file_path) as pdf:
            # Inspect first 3 pages
            for page in pdf.pages[:3]:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split("\n"):
                    clean_line = line.strip()
                    lower_line = clean_line.lower()
                    for header in standard_academic_headers:
                        if lower_line == header or lower_line.endswith(f" {header}"):
                            if clean_line not in detected_sections:
                                detected_sections.append(clean_line)

        raw_data: Dict[str, Any] = {
            "template_type": "RESEARCH_PAPER",
            "source_file_name": base_name,
            "color_palette": {
                "primary_hex": "#1B365D",
                "secondary_hex": "#4B6B94",
                "accent_hex": "#00A3E0",
                "background_hex": "#FFFFFF",
                "text_hex": "#222222"
            },
            "typography": {
                "heading_font": "Times New Roman",
                "body_font": "Times New Roman",
                "heading_sizes": {"title": 24, "h1": 18, "h2": 14, "h3": 12, "body": 11}
            },
            "layout_rules": {
                "slide_layouts_available": [],
                "max_bullets_per_slide": 5,
                "table_header_shading_hex": "#1B365D",
                "table_zebra_shading_hex": "#F4F7FA",
                "callout_box_style": "left_accent_border"
            },
            "detected_section_hierarchy": detected_sections if detected_sections else [
                "Abstract", "Introduction", "Methodology", "Results & Discussion", "Conclusion"
            ]
        }

        return normalize_guidance(raw_data)
    except Exception as e:
        print(f"Warning: PDF parsing error on {file_path}: {e}. Returning default theme.")
        return normalize_guidance()
