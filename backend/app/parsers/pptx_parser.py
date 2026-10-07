import os
import re
from typing import Optional, Dict, Any, List
from pptx import Presentation
from pptx.enum.dml import MSO_COLOR_TYPE
from ..shared.schemas.template_models import TemplateGuidanceProfile
from .template_normalizer import normalize_guidance

def parse_pptx_template(file_path: str) -> TemplateGuidanceProfile:
    """
    Inspects an uploaded PowerPoint (.pptx) template file.
    Extracts available slide layouts, font families, color theme hints,
    and detected slide section hierarchy from the template.
    """
    if not os.path.exists(file_path):
        return normalize_guidance()

    try:
        prs = Presentation(file_path)
        base_name = os.path.basename(file_path)

        available_layouts: List[str] = []
        detected_sections: List[str] = []
        extracted_fonts: List[str] = []
        extracted_colors: List[str] = []

        # 1. Inspect Slide Layouts
        for layout in prs.slide_layouts:
            name = layout.name.strip() if layout.name else "Custom Layout"
            if name not in available_layouts:
                available_layouts.append(name)

        # 2. Extract Titles & Section Structure from template slides
        for slide in prs.slides:
            # Check slide shapes for titles
            title_found = False
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        txt = paragraph.text.strip()
                        # Extract slide title candidate
                        if txt and len(txt) <= 70 and not txt.isdigit() and not title_found:
                            if txt not in detected_sections and not txt.startswith("By ") and len(txt) > 2:
                                detected_sections.append(txt)
                                title_found = True

                        # Safely inspect font
                        if paragraph.font and paragraph.font.name:
                            f_name = paragraph.font.name.strip()
                            if f_name and f_name not in extracted_fonts and not f_name.startswith("+"):
                                extracted_fonts.append(f_name)

                        # Safely inspect RGB color without crashing on _NoneColor
                        try:
                            if (
                                paragraph.font
                                and paragraph.font.color
                                and getattr(paragraph.font.color, "type", None) == MSO_COLOR_TYPE.RGB
                            ):
                                hex_col = f"#{paragraph.font.color.rgb}".upper()
                                if hex_col not in extracted_colors:
                                    extracted_colors.append(hex_col)
                        except Exception:
                            pass

        # 3. Inspect XML for Theme Colors and Typefaces (Master slides & layouts)
        xml_sources = [slide._element.xml for slide in list(prs.slides)[:5]]
        xml_sources += [layout._element.xml for layout in list(prs.slide_layouts)[:10]]
        if prs.slide_masters:
            xml_sources.append(prs.slide_masters[0]._element.xml)

        for xml_str in xml_sources:
            # Extract hex colors
            hex_matches = re.findall(r'val="([0-9A-Fa-f]{6})"', xml_str)
            for h in hex_matches:
                full_h = f"#{h.upper()}"
                if full_h not in extracted_colors:
                    extracted_colors.append(full_h)

            # Extract typefaces
            font_matches = re.findall(r'typeface="([^"]+)"', xml_str)
            for f in font_matches:
                f_clean = f.strip()
                if f_clean and not f_clean.startswith("+") and f_clean != "Wingdings" and f_clean not in extracted_fonts:
                    extracted_fonts.append(f_clean)

        # 4. Filter and select Brand Palette
        # Remove neutral black/white and dark near-black noise
        filtered_brand = [
            c for c in extracted_colors
            if c not in ["#FFFFFF", "#000000", "#100000", "#118000", "#135000", "#F4F7FA", "#F8FAFC", "#E8EBEE", "#EDEFF5"]
        ]

        def color_metrics(h: str):
            c = h.lstrip("#")
            r, g, b = int(c[0:2], 16) / 255.0, int(c[2:4], 16) / 255.0, int(c[4:6], 16) / 255.0
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            sat = 0.0 if max(r, g, b) == 0 else (max(r, g, b) - min(r, g, b)) / max(r, g, b)
            return lum, sat

        primary_hex = "#1B365D"
        secondary_hex = "#4B6B94"
        accent_hex = "#00A3E0"

        if filtered_brand:
            # Accent: vibrant color with high saturation and visible brightness
            vibrants = [c for c in filtered_brand if color_metrics(c)[1] > 0.45 and color_metrics(c)[0] > 0.3]
            if vibrants:
                accent_hex = vibrants[0]
            else:
                accent_hex = max(filtered_brand, key=lambda c: color_metrics(c)[1])

            # Primary: deep corporate tone (lum < 0.45), distinct from accent
            darks = [c for c in filtered_brand if color_metrics(c)[0] < 0.45 and c != accent_hex]
            if darks:
                primary_hex = darks[0]
            else:
                primary_hex = filtered_brand[0]

            # Secondary: mid-tone slate/support color
            mids = [c for c in filtered_brand if c != accent_hex and c != primary_hex and 0.2 <= color_metrics(c)[0] <= 0.65]
            if mids:
                secondary_hex = mids[0]
            elif len(filtered_brand) > 2:
                secondary_hex = [c for c in filtered_brand if c != accent_hex and c != primary_hex][0]

        heading_font = extracted_fonts[0] if extracted_fonts else "Calibri"
        body_font = extracted_fonts[1] if len(extracted_fonts) > 1 else heading_font

        raw_data: Dict[str, Any] = {
            "template_type": "PPTX",
            "source_file_name": base_name,
            "color_palette": {
                "primary_hex": primary_hex,
                "secondary_hex": secondary_hex,
                "accent_hex": accent_hex,
                "background_hex": "#FFFFFF",
                "text_hex": "#1E293B",
            },
            "typography": {
                "heading_font": heading_font,
                "body_font": body_font,
                "heading_sizes": {"title": 28, "h1": 22, "h2": 18, "h3": 14, "body": 12},
            },
            "layout_rules": {
                "slide_layouts_available": available_layouts if available_layouts else ["Title Slide", "Title and Content"],
                "max_bullets_per_slide": 5,
                "table_header_shading_hex": primary_hex,
                "table_zebra_shading_hex": "#F8FAFC",
                "callout_box_style": "left_accent_border",
            },
            "detected_section_hierarchy": detected_sections,
        }

        return normalize_guidance(raw_data)
    except Exception as e:
        print(f"Warning: PPTX parsing error on {file_path}: {e}. Returning default theme.")
        return normalize_guidance()

