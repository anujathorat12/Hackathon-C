"""
Builds a deck *inside* an uploaded PowerPoint template.

Instead of drawing our own design, the generated slides reuse the template's slide layouts, so
the logo, backgrounds, decorations, fonts, colours and footer come from the template itself.
The template's own sample slides teach us which layout is the cover and which is the content
layout, and which placeholder holds the title versus the body. The samples are then removed.
"""
import copy
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

from ...shared.schemas.template_models import DocumentControlMetadata, TemplateGuidanceProfile

TITLE_TYPES = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.VERTICAL_TITLE}
TEXT_TYPES = TITLE_TYPES | {PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.SUBTITLE}
MAX_CHARS_PER_SLIDE = 480  # keeps 20pt template bullets inside the body area
MAX_TABLE_ROWS_PER_SLIDE = 8

Roles = Tuple[int, Optional[int]]  # (title placeholder idx, body placeholder idx)


# ─── Learning the template ──────────────────────────────────────────────────────

def _text_placeholders(container) -> list:
    return [ph for ph in container.placeholders if ph.placeholder_format.type in TEXT_TYPES]


def _roles_from_sample(slide) -> Optional[Roles]:
    """How the template's own sample slide uses its placeholders: short top text = title, longest = body."""
    filled = [ph for ph in _text_placeholders(slide) if ph.has_text_frame and ph.text_frame.text.strip()]
    if not filled:
        return None
    titles = [ph for ph in filled if ph.placeholder_format.type in TITLE_TYPES]
    title = titles[0] if titles else min(
        filled, key=lambda ph: (len(ph.text_frame.paragraphs) > 1, ph.top or 0, len(ph.text_frame.text)))
    rest = [ph for ph in filled if ph.placeholder_format.idx != title.placeholder_format.idx]
    body = max(rest, key=lambda ph: len(ph.text_frame.text)) if rest else None
    return title.placeholder_format.idx, (body.placeholder_format.idx if body else None)


def _roles_from_layout(layout) -> Optional[Roles]:
    phs = _text_placeholders(layout)
    if not phs:
        return None
    titles = [ph for ph in phs if ph.placeholder_format.type in TITLE_TYPES]
    title = titles[0] if titles else min(phs, key=lambda ph: ph.top or 0)
    others = [ph for ph in phs if ph.placeholder_format.idx != title.placeholder_format.idx]
    body = max(others, key=lambda ph: (ph.width or 0) * (ph.height or 0)) if others else None
    return title.placeholder_format.idx, (body.placeholder_format.idx if body else None)


def _capture_style(slide, idx: Optional[int]) -> Optional[dict]:
    """Text styling a sample slide applies directly (fonts, bullets, sizes, autofit) — often richer than the layout's."""
    ph = next((p for p in slide.placeholders if p.placeholder_format.idx == idx), None) if idx is not None else None
    tx = ph._element.find(qn("p:txBody")) if ph is not None else None
    if tx is None:
        return None
    style = {"bodyPr": copy.deepcopy(tx.find(qn("a:bodyPr"))), "pPr": None, "rPr": None}
    for p in tx.findall(qn("a:p")):
        runs = p.findall(qn("a:r"))
        if runs and "".join(r.findtext(qn("a:t")) or "" for r in runs).strip():
            ppr = p.find(qn("a:pPr"))
            style["pPr"] = copy.deepcopy(ppr) if ppr is not None else None
            rpr = runs[0].find(qn("a:rPr"))
            if rpr is not None:
                rpr = copy.deepcopy(rpr)
                for attr in ("dirty", "err", "smtClean"):
                    rpr.attrib.pop(attr, None)
            style["rPr"] = rpr
            break
    return style


def _apply_style(placeholder, style: Optional[dict]):
    """Give our paragraphs the same paragraph/run properties the template's sample slide used."""
    if not style:
        return
    tx = placeholder._element.find(qn("p:txBody"))
    if style.get("bodyPr") is not None:
        old = tx.find(qn("a:bodyPr"))
        old.addprevious(copy.deepcopy(style["bodyPr"]))
        tx.remove(old)
    for p in tx.findall(qn("a:p")):
        old_ppr = p.find(qn("a:pPr"))
        lvl = old_ppr.get("lvl") if old_ppr is not None else None
        if style["pPr"] is not None:
            new_ppr = copy.deepcopy(style["pPr"])
            if lvl and lvl != "0":
                new_ppr.set("lvl", lvl)
                new_ppr.set("marL", str(int(new_ppr.get("marL", "342900")) + 457200 * int(lvl)))
            if old_ppr is not None:
                p.remove(old_ppr)
            p.insert(0, new_ppr)
        if style["rPr"] is not None:
            for r in p.findall(qn("a:r")):
                old_rpr = r.find(qn("a:rPr"))
                new_rpr = copy.deepcopy(style["rPr"])
                if old_rpr is not None and old_rpr.get("b") == "1":
                    new_rpr.set("b", "1")
                if old_rpr is not None:
                    r.remove(old_rpr)
                r.insert(0, new_rpr)


class TemplatePlan:
    def __init__(self, cover_layout, cover_roles: Roles, content_layout, content_roles: Roles, cover_textboxes: list,
                 styles: Optional[Dict[str, Optional[dict]]] = None):
        self.cover_layout = cover_layout
        self.cover_roles = cover_roles
        self.content_layout = content_layout
        self.content_roles = content_roles
        self.cover_textboxes = cover_textboxes
        self.styles = styles or {}


def analyse_template(prs) -> Optional[TemplatePlan]:
    """Pick cover and content layouts. Returns None when the template has no usable text layouts."""
    samples = list(prs.slides)

    # Content layout: the layout most used by the template's own content slides, if it has a body.
    content_layout, content_roles, content_sample = None, None, None
    by_layout: Dict[str, list] = {}
    for s in samples[1:]:
        by_layout.setdefault(s.slide_layout.name, []).append(s)
    for name, _ in Counter({k: len(v) for k, v in by_layout.items()}).most_common():
        sample = by_layout[name][0]
        roles = _roles_from_sample(sample) or _roles_from_layout(sample.slide_layout)
        if roles and roles[1] is not None:
            content_layout, content_roles, content_sample = sample.slide_layout, roles, sample
            break
    if content_layout is None:
        candidates = []
        for layout in prs.slide_layouts:
            roles = _roles_from_layout(layout)
            if roles and roles[1] is not None:
                name = layout.name.lower()
                score = (("content" in name) + ("bullet" in name) + ("text" in name)) * 10 - len(_text_placeholders(layout))
                candidates.append((score, layout, roles))
        if candidates:
            _, content_layout, content_roles = max(candidates, key=lambda c: c[0])
    if content_layout is None:
        return None

    # Cover layout: the first sample slide's layout, else a layout named like a title slide.
    cover_layout, cover_roles, cover_textboxes = None, None, []
    if samples:
        cover_layout = samples[0].slide_layout
        cover_roles = _roles_from_sample(samples[0]) or _roles_from_layout(cover_layout)
        cover_textboxes = [copy.deepcopy(sh._element) for sh in samples[0].shapes
                           if not sh.is_placeholder and sh.has_text_frame and sh.text_frame.text.strip()][:1]
    if not cover_roles:
        for layout in prs.slide_layouts:
            roles = _roles_from_layout(layout)
            if roles and "title" in layout.name.lower():
                cover_layout, cover_roles = layout, roles
                break
    if not cover_roles:
        cover_layout, cover_roles = content_layout, content_roles

    styles = {}
    if content_sample is not None:
        styles["content_title"] = _capture_style(content_sample, content_roles[0])
        styles["content_body"] = _capture_style(content_sample, content_roles[1])
    if samples and cover_layout is samples[0].slide_layout:
        styles["cover_title"] = _capture_style(samples[0], cover_roles[0])
        styles["cover_sub"] = _capture_style(samples[0], cover_roles[1])
    return TemplatePlan(cover_layout, cover_roles, content_layout, content_roles, cover_textboxes, styles)


# ─── Markdown → slide content ───────────────────────────────────────────────────

Item = Tuple[str, int, bool]  # (text, indent level, is sub-heading)


def _sentences(paragraph: str) -> List[str]:
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"“(\[])', paragraph.strip())
    return [p.strip() for p in parts if p.strip()]


def parse_markdown(md: str) -> Tuple[Optional[str], List[str], List[Tuple[str, list]]]:
    """Returns (document title, intro sentences, sections). A section's blocks are items or tables."""
    title, intro, sections = None, [], []
    intro_blocks: list = []
    blocks = intro_blocks
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        i += 1
        if not line or line in ("---", "***") or line.startswith("<!--"):
            continue
        if line.startswith("|"):
            table = [line]
            while i < len(lines) and lines[i].strip().startswith("|"):
                table.append(lines[i].strip())
                i += 1
            rows = [[c.strip() for c in r.strip("|").split("|")] for r in table
                    if not re.fullmatch(r"\|?[\s:\-|]+\|?", r)]
            if len(rows) >= 2:
                blocks.append(("table", rows[0], rows[1:]))
            continue
        if line.startswith("# ") and title is None and not sections:
            title = line[2:].strip()
        elif line.startswith("## ") or line.startswith("# "):
            blocks = []
            sections.append((line.lstrip("#").strip(), blocks))
        elif line.startswith("###"):
            blocks.append(("item", (line.lstrip("#").strip(), 0, True)))
        elif re.match(r"^([-*+]|\d+[.)])\s+", line):
            level = 1 if len(raw) - len(raw.lstrip()) >= 2 else 0
            blocks.append(("item", (re.sub(r"^([-*+]|\d+[.)])\s+", "", line), level, False)))
        elif line.startswith(">"):
            blocks.append(("item", (line.lstrip("> ").strip(), 0, False)))
        else:
            for sentence in _sentences(line):
                blocks.append(("item", (sentence, 0, False)))
    intro = [b[1][0] for b in intro_blocks if b[0] == "item"]
    return title, intro, sections


def paginate(heading: str, blocks: list, max_bullets: int) -> List[Tuple[str, str, object]]:
    """Split a section into slides: ('bullets', title, [items]) or ('table', title, (header, rows))."""
    slides, group, chars = [], [], 0

    def flush():
        nonlocal group, chars
        if group:
            slides.append(("bullets", heading, group))
        group, chars = [], 0

    for kind, *data in blocks:
        if kind == "table":
            flush()
            header, rows = data
            for start in range(0, len(rows), MAX_TABLE_ROWS_PER_SLIDE):
                slides.append(("table", heading, (header, rows[start:start + MAX_TABLE_ROWS_PER_SLIDE])))
            continue
        item = data[0]
        if group and (len(group) >= max_bullets or chars + len(item[0]) > MAX_CHARS_PER_SLIDE):
            flush()
        group.append(item)
        chars += len(item[0])
    flush()
    if not slides:
        slides.append(("bullets", heading, []))
    # Number continuation slides so the audience can follow a long section.
    return [(k, t if n == 0 else f"{t} (cont.)", d) for n, (k, t, d) in enumerate(slides)]


# ─── Writing into placeholders ──────────────────────────────────────────────────

def _clean(text: str) -> str:
    return re.sub(r"[`_]{1,2}|(?<!\*)\*(?!\*)", "", text).strip()


def _write_runs(paragraph, text: str, bold: bool = False):
    """Add text as runs, honouring **bold** markup, without overriding the template's styling."""
    for n, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not part:
            continue
        run = paragraph.add_run()
        run.text = _clean(part)
        if bold or n % 2 == 1:
            run.font.bold = True


def _set_items(text_frame, items: List[Item]):
    text_frame.clear()
    for n, (text, level, is_sub) in enumerate(items):
        p = text_frame.paragraphs[0] if n == 0 else text_frame.add_paragraph()
        p.level = min(level, 4)
        _write_runs(p, text, bold=is_sub)


def _set_text(placeholder, text: str):
    tf = placeholder.text_frame
    tf.clear()
    _write_runs(tf.paragraphs[0], text)


def _placeholder(slide, idx: Optional[int]):
    if idx is None:
        return None
    return next((ph for ph in slide.placeholders if ph.placeholder_format.idx == idx), None)


def _remove_empty_placeholders(slide, keep: set):
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx not in keep and ph.has_text_frame and not ph.text_frame.text.strip():
            ph._element.getparent().remove(ph._element)


def _add_slide_number(slide, layout):
    """python-pptx doesn't instantiate slide-number placeholders; copy the layout's so numbering shows."""
    for ph in layout.placeholders:
        if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
            slide.shapes._spTree.append(copy.deepcopy(ph._element))


def _retext_textbox(sp, lines: List[str]):
    """Reuse a styled textbox from the template's cover (e.g. the author line) with new text."""
    tx = sp.find(qn("p:txBody"))
    paras = tx.findall(qn("a:p"))
    proto_p = copy.deepcopy(paras[0])
    runs = proto_p.findall(qn("a:r"))
    proto_r = copy.deepcopy(runs[0]) if runs else None
    for p in paras:
        tx.remove(p)
    for line in lines:
        p = copy.deepcopy(proto_p)
        for child in list(p):
            if child.tag in (qn("a:r"), qn("a:br"), qn("a:fld")):
                p.remove(child)
        if proto_r is not None:
            r = copy.deepcopy(proto_r)
            r.find(qn("a:t")).text = line
            end = p.find(qn("a:endParaRPr"))
            if end is not None:
                end.addprevious(r)
            else:
                p.append(r)
        tx.append(p)


def _remove_all_slides(prs):
    id_list = prs.slides._sldIdLst
    for sld_id in list(id_list):
        prs.part.drop_rel(sld_id.rId)
        id_list.remove(sld_id)


def _add_table(slide, body, header: List[str], rows: List[List[str]]):
    left, top, width, height = body.left, body.top, body.width, body.height
    body._element.getparent().remove(body._element)
    cols = max(len(header), max((len(r) for r in rows), default=0))
    row_h = Emu(int(Pt(30)))
    frame = slide.shapes.add_table(len(rows) + 1, cols, left, top, width, Emu(min(int(height), int(row_h) * (len(rows) + 1))))
    table = frame.table
    for r, values in enumerate([header] + rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = ""
            _write_runs(cell.text_frame.paragraphs[0], values[c] if c < len(values) else "", bold=(r == 0))
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(12 if r else 13)


# ─── Entry point ────────────────────────────────────────────────────────────────

def build_deck_in_template(markdown: str, output_path: str, metadata: DocumentControlMetadata,
                           guidance: TemplateGuidanceProfile, template_path: str,
                           speaker_notes: Optional[Dict[str, str]] = None) -> bool:
    """Build the deck inside the template. Returns False (caller falls back) if the template has no usable layouts."""
    prs = Presentation(template_path)
    plan = analyse_template(prs)
    if plan is None:
        print(f"[Template Deck] '{template_path}' has no usable text layouts; using the built-in design.")
        return False

    doc_title, intro, sections = parse_markdown(markdown)
    doc_title = metadata.document_title or doc_title or "Presentation"
    if intro and not sections:
        sections = [("Overview", [("item", (s, 0, False)) for s in intro])]
        intro = []
    max_bullets = max(3, guidance.layout_rules.max_bullets_per_slide or 5)

    _remove_all_slides(prs)

    # Cover slide
    cover = prs.slides.add_slide(plan.cover_layout)
    title_idx, sub_idx = plan.cover_roles
    title_ph = _placeholder(cover, title_idx)
    if title_ph is not None:
        _set_text(title_ph, doc_title)
        _apply_style(title_ph, plan.styles.get("cover_title"))
    subtitle = intro[0] if intro and len(intro[0]) <= 180 else None
    sub_ph = _placeholder(cover, sub_idx)
    if sub_ph is not None:
        _set_text(sub_ph, subtitle or f"{metadata.date}")
        _apply_style(sub_ph, plan.styles.get("cover_sub"))
    for sp in plan.cover_textboxes:
        cover.shapes._spTree.append(sp)
        _retext_textbox(sp, ["By AGENT-101", metadata.date])
    _remove_empty_placeholders(cover, keep={title_idx, sub_idx})
    _add_slide_number(cover, plan.cover_layout)

    # Intro sentences that didn't fit the cover become an overview slide.
    remaining_intro = intro[1:] if subtitle else intro
    if remaining_intro:
        sections.insert(0, ("Overview", [("item", (s, 0, False)) for s in remaining_intro]))

    c_title_idx, c_body_idx = plan.content_roles
    for heading, blocks in sections:
        for n, (kind, slide_title, data) in enumerate(paginate(heading, blocks, max_bullets)):
            slide = prs.slides.add_slide(plan.content_layout)
            note = (speaker_notes or {}).get(heading)
            if note and n == 0:
                slide.notes_slide.notes_text_frame.text = note
            ph = _placeholder(slide, c_title_idx)
            if ph is not None:
                _set_text(ph, slide_title)
                _apply_style(ph, plan.styles.get("content_title"))
            body = _placeholder(slide, c_body_idx)
            if body is not None:
                if kind == "table":
                    _add_table(slide, body, *data)
                else:
                    _set_items(body.text_frame, data)
                    _apply_style(body, plan.styles.get("content_body"))
            _remove_empty_placeholders(slide, keep={c_title_idx, c_body_idx})
            _add_slide_number(slide, plan.content_layout)

    prs.save(output_path)
    print(f"[Template Deck] Built {len(prs.slides)} slides inside template layouts "
          f"('{plan.cover_layout.name}' cover, '{plan.content_layout.name}' content): {output_path}")
    return True
