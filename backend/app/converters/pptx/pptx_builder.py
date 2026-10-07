import os
import re
from typing import Dict, List, Optional, Tuple
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from ...shared.schemas.template_models import DocumentControlMetadata, TemplateGuidanceProfile
from .theme_styler import pptx_hex_to_rgb, apply_text_styling

def parse_stat_metric(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Detects if a bullet point represents a KPI / stat metric.
    e.g., "* **Triage Latency:** Completed in 142 seconds (Target: < 180s)"
    Returns: (Metric Title, Highlight Number/Phrase, Sub-detail) or None
    """
    match = re.match(r'^\*\*(.*?)\:\*\*\s*(.*)$', text.strip())
    if not match:
        return None
    
    title = match.group(1).strip()
    rest = match.group(2).strip()

    # Try to extract leading number/metric (e.g. "142 seconds", "99.8%", "100%", "7.2:1")
    stat_match = re.search(r'(\d+(?:\.\d+)?(?:%|s|x|:1)?(?:\s*(?:seconds|min|ms|hrs|GB|MB))?)', rest, re.IGNORECASE)
    if stat_match:
        highlight = stat_match.group(1).strip()
        detail = rest.replace(highlight, "").strip()
        detail = re.sub(r'^[,\-\s(]+', '', detail).rstrip(')')
    else:
        highlight = rest[:20]
        detail = rest[20:].strip()

    return (title, highlight, detail)

def build_pptx_deliverable(
    markdown_content: str,
    output_path: str,
    metadata: Optional[DocumentControlMetadata] = None,
    guidance: Optional[TemplateGuidanceProfile] = None,
    speaker_notes: Optional[Dict[str, str]] = None
) -> str:
    """
    Compiles refined markdown into an elite, publication-ready PowerPoint presentation.
    Design Highlights:
      1. Formal Cover Slide with Pill Badge, High-Contrast Typography, and Metadata Grid.
      2. KPI / Stat Grid Slides: Automatically turns bulleted metrics into modern vector stat cards.
      3. Content Slides: Slide header with accent underline bar, clean bullet cards, and running footer.
      4. 16:9 Widescreen aspect ratio (13.33 x 7.5 inches).
    """
    if metadata is None:
        metadata = DocumentControlMetadata()
    if guidance is None:
        from ...parsers.template_normalizer import DEFAULT_CORPORATE_THEME
        guidance = DEFAULT_CORPORATE_THEME

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Brand-faithful path: build inside the uploaded template's own layouts when it has usable ones.
    template_path = guidance.source_file_path
    if template_path and template_path.lower().endswith(".pptx") and os.path.exists(template_path):
        from .template_deck_builder import build_deck_in_template
        try:
            if build_deck_in_template(markdown_content, output_path, metadata, guidance, template_path, speaker_notes):
                return output_path
        except Exception as e:
            print(f"[PPTX Builder] Template build failed ({e}); using the built-in design.")

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    primary_hex = guidance.color_palette.primary_hex
    secondary_hex = guidance.color_palette.secondary_hex
    accent_hex = guidance.color_palette.accent_hex
    font_heading = guidance.typography.heading_font
    font_body = guidance.typography.body_font

    primary_rgb = pptx_hex_to_rgb(primary_hex)
    secondary_rgb = pptx_hex_to_rgb(secondary_hex)
    accent_rgb = pptx_hex_to_rgb(accent_hex)

    # Split markdown into slide chunks
    slide_chunks: List[str] = []
    if "<!-- slide -->" in markdown_content:
        for chunk in markdown_content.split("<!-- slide -->"):
            if chunk.strip():
                slide_chunks.append(chunk.strip())
    else:
        lines = markdown_content.split('\n')
        current_chunk: List[str] = []
        for line in lines:
            if line.startswith('# ') or line.startswith('## '):
                if current_chunk:
                    slide_chunks.append('\n'.join(current_chunk).strip())
                    current_chunk = []
            current_chunk.append(line)
        if current_chunk:
            slide_chunks.append('\n'.join(current_chunk).strip())

    if not slide_chunks:
        slide_chunks = [markdown_content]

    # =========================================================================
    # SLIDE 1: ELITE COVER TITLE SLIDE (Dark Luxury Navy Theme)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)

    # 1. Dark Background Canvas
    bg_shape = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.33), Inches(7.5))
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = pptx_hex_to_rgb("#0A192F")
    bg_shape.line.fill.background()

    # 2. Left Accent Vertical Brand Pillar
    pillar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.35), Inches(7.5))
    pillar.fill.solid()
    pillar.fill.fore_color.rgb = accent_rgb
    pillar.line.fill.background()

    # 3. Pill Badge (System ID)
    badge = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(3.8), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = pptx_hex_to_rgb("#172A45")
    badge.line.color.rgb = accent_rgb
    badge.line.width = Pt(1)
    b_tf = badge.text_frame
    b_tf.word_wrap = False
    bp = b_tf.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    apply_text_styling(bp, f"PRESENTATION  •  {metadata.date}".upper(), font_name=font_heading, font_size_pt=10, color_hex=accent_hex, bold=True)

    # 4. Main Cover Title
    title_text = metadata.document_title
    first_lines = slide_chunks[0].split('\n')
    if first_lines and first_lines[0].startswith('# '):
        title_text = first_lines[0][2:].strip()

    title_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.9), Inches(11.0), Inches(2.2))
    t_tf = title_box.text_frame
    t_tf.word_wrap = True
    tp = t_tf.paragraphs[0]
    apply_text_styling(tp, title_text, font_name=font_heading, font_size_pt=38, color_hex="#FFFFFF", bold=True)

    # 5. Subtitle & Objective
    sub_box = slide1.shapes.add_textbox(Inches(1.2), Inches(4.3), Inches(11.0), Inches(1.2))
    s_tf = sub_box.text_frame
    s_tf.word_wrap = True
    sp = s_tf.paragraphs[0]
    sub_content = metadata.author
    apply_text_styling(sp, sub_content, font_name=font_body, font_size_pt=15, color_hex="#8892B0", bold=False)

    # 6. Bottom Metadata Strip
    meta_box = slide1.shapes.add_textbox(Inches(1.2), Inches(6.2), Inches(11.0), Inches(0.6))
    m_tf = meta_box.text_frame
    mp = m_tf.paragraphs[0]
    meta_text = f"Version {metadata.version}   |   {metadata.date}"
    apply_text_styling(mp, meta_text, font_name=font_body, font_size_pt=10, color_hex="#64FFDA", bold=True)

    # Determine dark vs light mode for content canvas
    bg_hex = guidance.color_palette.background_hex or "#FBFDFF"
    bg_clean = bg_hex.lstrip('#')
    is_dark_deck = False
    if len(bg_clean) == 6:
        r_b, g_b, b_b = int(bg_clean[:2], 16), int(bg_clean[2:4], 16), int(bg_clean[4:6], 16)
        if (0.2126 * r_b + 0.7152 * g_b + 0.0722 * b_b) < 130:
            is_dark_deck = True

    canvas_bg_hex = bg_hex if is_dark_deck else "#FBFDFF"
    text_color_hex = "#FFFFFF" if is_dark_deck else "#2D3748"
    card_bg_hex = "#252530" if is_dark_deck else "#FFFFFF"
    card_border_hex = "#3F3F52" if is_dark_deck else "#EDF2F7"
    header_color_hex = "#FFFFFF" if is_dark_deck else primary_hex

    # =========================================================================
    # BODY SLIDES (SLIDES 2+): KPI STAT CARDS & STRUCTURED CONTENT
    # =========================================================================
    for slide_idx, chunk in enumerate(slide_chunks[1:], start=2):
        # Horizontal rules ("---") are section separators in markdown, not slide content.
        lines = [l.strip() for l in chunk.split('\n') if l.strip() and l.strip() not in ("---", "***", "___")]
        if not lines:
            continue

        slide = prs.slides.add_slide(blank_layout)

        # 1. Canvas Background (Adaptive Dark/Light)
        canvas = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.33), Inches(7.5))
        canvas.fill.solid()
        canvas.fill.fore_color.rgb = pptx_hex_to_rgb(canvas_bg_hex)
        canvas.line.fill.background()

        # 2. Extract Slide Title
        slide_title = "Executive Architecture"
        content_lines: List[str] = []

        for line in lines:
            if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
                slide_title = line.lstrip('# ').strip()
            elif line.startswith('* ') or line.startswith('- '):
                content_lines.append(line[2:].strip())
            elif line.startswith('>'):
                content_lines.append(f"Standard: {line.lstrip('> ').strip()}")
            elif not line.startswith('|'):
                content_lines.append(line)

        note = (speaker_notes or {}).get(slide_title)
        if note:
            slide.notes_slide.notes_text_frame.text = note

        # 3. Slide Header Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.5), Inches(0.9))
        t_tf = title_box.text_frame
        t_tf.word_wrap = True
        tp = t_tf.paragraphs[0]
        apply_text_styling(tp, slide_title, font_name=font_heading, font_size_pt=26, color_hex=header_color_hex, bold=True)

        # Accent Underline Bar
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(2.5), Inches(0.06))
        bar.fill.solid()
        bar.fill.fore_color.rgb = accent_rgb
        bar.line.fill.background()

        # 4. Check if Content represents KPI Stat Metrics
        stat_items: List[Tuple[str, str, str]] = []
        for c_line in content_lines:
            stat = parse_stat_metric(c_line)
            if stat:
                stat_items.append(stat)

        # If 3 or more stat metrics detected, render as KPI Stat Cards!
        if len(stat_items) >= 3:
            num_cards = min(len(stat_items), 4)
            card_spacing = 0.3
            total_margin = 0.8 * 2
            available_width = 13.33 - total_margin - (card_spacing * (num_cards - 1))
            card_w = available_width / num_cards
            card_h = 4.2
            top_pos = 1.9

            for i in range(num_cards):
                s_title, s_num, s_desc = stat_items[i]
                left_pos = 0.8 + i * (card_w + card_spacing)

                # Card Shape
                card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left_pos), Inches(top_pos), Inches(card_w), Inches(card_h))
                card.fill.solid()
                card.fill.fore_color.rgb = pptx_hex_to_rgb(card_bg_hex)
                card.line.color.rgb = pptx_hex_to_rgb(card_border_hex)
                card.line.width = Pt(1.5)

                # Top colored pill inside card
                pill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_pos), Inches(top_pos), Inches(card_w), Inches(0.12))
                pill.fill.solid()
                pill.fill.fore_color.rgb = accent_rgb
                pill.line.fill.background()

                # Card Text
                ctf = card.text_frame
                ctf.word_wrap = True
                ctf.margin_left = Inches(0.25)
                ctf.margin_right = Inches(0.25)
                ctf.margin_top = Inches(0.35)

                # Metric Title
                p1 = ctf.paragraphs[0]
                apply_text_styling(p1, s_title.upper(), font_name=font_heading, font_size_pt=11, color_hex=accent_hex if is_dark_deck else secondary_hex, bold=True)
                p1.space_after = Pt(14)

                # Big Number Callout
                p2 = ctf.add_paragraph()
                apply_text_styling(p2, s_num, font_name=font_heading, font_size_pt=32, color_hex=header_color_hex, bold=True)
                p2.space_after = Pt(14)

                # Description
                if s_desc:
                    p3 = ctf.add_paragraph()
                    apply_text_styling(p3, s_desc, font_name=font_body, font_size_pt=11.5, color_hex="#A0AEC0" if is_dark_deck else "#555555")

        else:
            # Standard Structured Content: Render as Card List
            num_items = min(len(content_lines), guidance.layout_rules.max_bullets_per_slide)
            if not num_items:
                content_lines = ["Autonomous synthesis completed according to enterprise specifications."]
                num_items = 1

            item_h = min(0.9, 4.4 / num_items)
            spacing = 0.2

            for i in range(num_items):
                item_text = content_lines[i]
                clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', item_text)
                card_top = 1.8 + i * (item_h + spacing)

                # Item Card
                row_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(card_top), Inches(11.73), Inches(item_h))
                row_card.fill.solid()
                row_card.fill.fore_color.rgb = pptx_hex_to_rgb(card_bg_hex)
                row_card.line.color.rgb = pptx_hex_to_rgb(card_border_hex)
                row_card.line.width = Pt(1)

                # Left Indicator Dot / Accent
                dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.1), Inches(card_top + (item_h/2) - 0.08), Inches(0.16), Inches(0.16))
                dot.fill.solid()
                dot.fill.fore_color.rgb = accent_rgb
                dot.line.fill.background()

                # Text Frame
                rc_tf = row_card.text_frame
                rc_tf.word_wrap = True
                rc_tf.margin_left = Inches(0.7)
                rc_tf.margin_top = Inches(0.15)
                rc_tf.margin_right = Inches(0.3)
                rp = rc_tf.paragraphs[0]
                apply_text_styling(rp, clean_text, font_name=font_body, font_size_pt=14, color_hex=text_color_hex)

        # 5. Running Footer on Slide (Pages 2+)
        footer_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.8), Inches(11.73), Inches(0.02))
        footer_line.fill.solid()
        footer_line.fill.fore_color.rgb = accent_rgb if is_dark_deck else pptx_hex_to_rgb("#E2E8F0")
        footer_line.line.fill.background()

        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.88), Inches(8.0), Inches(0.4))
        ftp = footer_box.text_frame.paragraphs[0]
        apply_text_styling(ftp, metadata.document_title, font_name=font_body, font_size_pt=9, color_hex="#818CF8" if is_dark_deck else "#A0AEC0")

        num_box = slide.shapes.add_textbox(Inches(10.5), Inches(6.88), Inches(2.0), Inches(0.4))
        np = num_box.text_frame.paragraphs[0]
        np.alignment = PP_ALIGN.RIGHT
        apply_text_styling(np, f"SLIDE {slide_idx}", font_name=font_body, font_size_pt=9, color_hex="#818CF8" if is_dark_deck else "#A0AEC0", bold=True)

    prs.save(output_path)
    print(f"[PPTX Builder] Successfully generated presentation: {output_path}")
    return output_path
