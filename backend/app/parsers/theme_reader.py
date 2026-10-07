"""
Reads the brand colours and fonts an Office template defines in its theme (theme*.xml).

Corporate templates keep their identity in the theme and slide masters rather than on sample
slides, so this is the most reliable source when the theme has been customised. Stock Office
themes are detected so callers can fall back to inspecting the slides instead.
"""
import re
import zipfile
from typing import Dict, Optional

# accent1 of the stock Office themes (2007-2010, 2013-2022, 2023+). A theme using one of these
# was almost certainly not customised for the brand.
STOCK_ACCENT1 = {"4F81BD", "4472C4", "156082", "5B9BD5"}

COLOR_SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6"]


def _luminance(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _saturation(hex_color: str) -> int:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return max(r, g, b) - min(r, g, b)


def parse_theme_xml(xml: str) -> Optional[Dict]:
    colors = {}
    for slot in COLOR_SLOTS:
        m = re.search(rf"<a:{slot}>.*?(?:srgbClr val|lastClr)=\"([0-9A-Fa-f]{{6}})\"", xml, re.S)
        if m:
            colors[slot] = m.group(1).upper()
    if "accent1" not in colors:
        return None
    major = re.search(r"<a:majorFont>\s*<a:latin typeface=\"([^\"]*)\"", xml)
    minor = re.search(r"<a:minorFont>\s*<a:latin typeface=\"([^\"]*)\"", xml)
    return {
        "colors": colors,
        "heading_font": (major.group(1) if major and major.group(1) else None),
        "body_font": (minor.group(1) if minor and minor.group(1) else None),
        "is_stock": colors["accent1"] in STOCK_ACCENT1,
    }


def read_theme(file_path: str) -> Optional[Dict]:
    """Theme of a .pptx (first slide master's theme) or .docx file, or None if unreadable."""
    try:
        with zipfile.ZipFile(file_path) as z:
            names = z.namelist()
            theme_name = None
            if file_path.lower().endswith(".pptx"):
                # Follow slideMaster1 -> theme so multi-theme decks use the master actually applied.
                rels = "ppt/slideMasters/_rels/slideMaster1.xml.rels"
                if rels in names:
                    m = re.search(r'Target="\.\./theme/(theme\d+\.xml)"', z.read(rels).decode("utf8", "ignore"))
                    if m:
                        theme_name = f"ppt/theme/{m.group(1)}"
                theme_name = theme_name or next((n for n in names if re.match(r"ppt/theme/theme\d+\.xml$", n)), None)
            else:
                theme_name = next((n for n in names if re.match(r"word/theme/theme\d+\.xml$", n)), None)
            if not theme_name or theme_name not in names:
                return None
            return parse_theme_xml(z.read(theme_name).decode("utf8", "ignore"))
    except Exception:
        return None


def palette_from_theme(theme: Dict) -> Dict[str, str]:
    """Map theme colour slots onto the platform's palette roles."""
    c = theme["colors"]
    accents = [c[k] for k in ("accent1", "accent2", "accent3", "accent4", "accent5", "accent6") if k in c]

    # Accent: the first vivid accent (brand highlight colour).
    accent = next((a for a in accents if _saturation(a) > 60 and 40 < _luminance(a) < 230), accents[0])
    # Primary (headings): the darkest coloured accent, else dk2 — e.g. a brand navy.
    dark_coloured = sorted((a for a in accents if _luminance(a) < 110 and _saturation(a) > 25), key=_luminance)
    primary = dark_coloured[0] if dark_coloured else c.get("dk2", "1B365D")
    secondary = c.get("dk2", primary)
    return {
        "primary_hex": f"#{primary}",
        "secondary_hex": f"#{secondary}",
        "accent_hex": f"#{accent}",
        "background_hex": f"#{c.get('lt1', 'FFFFFF')}",
        "text_hex": f"#{c.get('dk1', '222222')}",
    }
