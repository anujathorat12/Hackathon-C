from pptx.dml.color import RGBColor
from pptx.util import Pt
from ...shared.schemas.template_models import TemplateGuidanceProfile

def pptx_hex_to_rgb(hex_str: str) -> RGBColor:
    hex_clean = hex_str.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join([c*2 for c in hex_clean])
    return RGBColor(int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16))

def apply_text_styling(paragraph, text: str, font_name: str, font_size_pt: int, color_hex: str, bold: bool = False):
    paragraph.text = text
    # Style both the paragraph defaults and each run: PowerPoint honours either, but some renderers
    # (e.g. the in-browser preview) only read run-level properties.
    for font in [paragraph.font] + [run.font for run in paragraph.runs]:
        font.name = font_name
        font.size = Pt(font_size_pt)
        font.bold = bold
        font.color.rgb = pptx_hex_to_rgb(color_hex)
