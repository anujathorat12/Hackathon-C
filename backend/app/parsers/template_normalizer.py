from typing import Dict, Any, Optional
from ..shared.schemas.template_models import (
    TemplateGuidanceProfile,
    ColorPalette,
    Typography,
    LayoutRules
)

DEFAULT_CORPORATE_THEME = TemplateGuidanceProfile(
    template_type="DEFAULT",
    color_palette=ColorPalette(
        primary_hex="#1B365D",
        secondary_hex="#4B6B94",
        accent_hex="#00A3E0",
        background_hex="#FFFFFF",
        text_hex="#222222"
    ),
    typography=Typography(
        heading_font="Calibri",
        body_font="Calibri",
        heading_sizes={"title": 26, "h1": 20, "h2": 15, "h3": 12, "body": 11}
    ),
    layout_rules=LayoutRules(
        slide_layouts_available=["Title", "Title and Content", "Two Content", "Section Header"],
        max_bullets_per_slide=5,
        table_header_shading_hex="#1B365D",
        table_zebra_shading_hex="#F4F7FA",
        callout_box_style="left_accent_border"
    ),
    detected_section_hierarchy=[
        "Executive Summary",
        "System Architecture",
        "Implementation & Methodology",
        "Performance Benchmarks",
        "Conclusion & Next Steps"
    ]
)

def normalize_guidance(raw_data: Optional[Dict[str, Any]] = None) -> TemplateGuidanceProfile:
    """
    Normalizes raw extracted template data into a validated TemplateGuidanceProfile.
    Falls back gracefully to enterprise corporate defaults if raw data is missing or partial.
    """
    if not raw_data:
        return DEFAULT_CORPORATE_THEME.model_copy()

    try:
        color_data = raw_data.get("color_palette", {})
        palette = ColorPalette(
            primary_hex=color_data.get("primary_hex", "#1B365D"),
            secondary_hex=color_data.get("secondary_hex", "#4B6B94"),
            accent_hex=color_data.get("accent_hex", "#00A3E0"),
            background_hex=color_data.get("background_hex", "#FFFFFF"),
            text_hex=color_data.get("text_hex", "#222222")
        )

        typo_data = raw_data.get("typography", {})
        typography = Typography(
            heading_font=typo_data.get("heading_font", "Calibri"),
            body_font=typo_data.get("body_font", "Calibri"),
            heading_sizes=typo_data.get("heading_sizes", {"title": 26, "h1": 20, "h2": 15, "h3": 12, "body": 11})
        )

        layout_data = raw_data.get("layout_rules", {})
        layout_rules = LayoutRules(
            slide_layouts_available=layout_data.get("slide_layouts_available", ["Title", "Title and Content"]),
            max_bullets_per_slide=layout_data.get("max_bullets_per_slide", 5),
            table_header_shading_hex=layout_data.get("table_header_shading_hex", palette.primary_hex),
            table_zebra_shading_hex=layout_data.get("table_zebra_shading_hex", "#F4F7FA"),
            callout_box_style=layout_data.get("callout_box_style", "left_accent_border")
        )

        return TemplateGuidanceProfile(
            template_type=raw_data.get("template_type", "DEFAULT"),
            source_file_name=raw_data.get("source_file_name"),
            color_palette=palette,
            typography=typography,
            layout_rules=layout_rules,
            detected_section_hierarchy=raw_data.get("detected_section_hierarchy", [])
        )
    except Exception:
        return DEFAULT_CORPORATE_THEME.model_copy()
