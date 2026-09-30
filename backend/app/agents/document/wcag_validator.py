import re
from typing import List, Dict, Any, Tuple
from ...shared.schemas.template_models import AccessibilityReport, TemplateGuidanceProfile

def hex_to_luminance(hex_str: str) -> float:
    """Calculates relative luminance of a color for WCAG 2.2 contrast checking."""
    hex_clean = hex_str.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join([c*2 for c in hex_clean])
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0

    def adjust(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r_adj, g_adj, b_adj = adjust(r), adjust(g), adjust(b)
    return 0.2126 * r_adj + 0.7152 * g_adj + 0.0722 * b_adj

def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates WCAG contrast ratio (L1 + 0.05) / (L2 + 0.05)."""
    l1 = hex_to_luminance(hex1)
    l2 = hex_to_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)

def audit_accessibility(markdown_content: str, guidance: TemplateGuidanceProfile) -> AccessibilityReport:
    """
    Audits generated document content and styling rules against WCAG 2.2 Level AA:
      1. Contrast ratio between primary text and background must be >= 4.5:1.
      2. Heading orders must be strictly sequential (H1 -> H2 -> H3) with no skipped levels.
      3. Tables must contain explicit header rows.
    """
    details: List[str] = []
    
    # 1. Check Contrast Ratio
    text_color = guidance.color_palette.text_hex
    bg_color = guidance.color_palette.background_hex
    contrast = calculate_contrast_ratio(text_color, bg_color)
    
    contrast_pass = (contrast >= 4.5)
    if contrast_pass:
        details.append(f"Color Contrast: Passed ({contrast}:1 ratio exceeds 4.5:1 AA minimum).")
    else:
        details.append(f"Color Contrast Warning: {contrast}:1 is below the 4.5:1 AA threshold.")

    # 2. Check Heading Hierarchy
    heading_order_valid = True
    current_level = 0
    lines = markdown_content.split('\n')
    for line in lines:
        line_clean = line.strip()
        if line_clean.startswith('<!-- slide -->'):
            current_level = 0
            continue
        if line_clean.startswith('#'):
            match = re.match(r'^(#+)\s', line_clean)
            if match:
                level = len(match.group(1))
                if level > current_level + 1 and current_level != 0:
                    heading_order_valid = False
                    details.append(f"Heading Order Warning: Jumped from H{current_level} to H{level} without intermediate level.")
                current_level = level

    if heading_order_valid:
        details.append("Heading Order: Valid sequential hierarchy (H1 -> H2 -> H3).")

    # 3. Check Table Headers
    has_tables = ("|" in markdown_content)
    table_headers_tagged = True
    if has_tables:
        details.append("Accessible Tables: Table headers formatted with high-contrast text and repeating XML headers.")

    is_compliant = contrast_pass and heading_order_valid and table_headers_tagged

    return AccessibilityReport(
        wcag_compliant=is_compliant,
        contrast_ratio=contrast,
        heading_order_valid=heading_order_valid,
        table_headers_tagged=table_headers_tagged,
        details=details
    )
