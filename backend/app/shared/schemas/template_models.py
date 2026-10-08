import datetime
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field

class ColorPalette(BaseModel):
    primary_hex: str = Field(default="#1B365D", description="Main heading & brand accent color")
    secondary_hex: str = Field(default="#4B6B94", description="Subheading and secondary accent")
    accent_hex: str = Field(default="#00A3E0", description="Highlight, border, or callout color")
    background_hex: str = Field(default="#FFFFFF", description="Document or slide background")
    text_hex: str = Field(default="#222222", description="Primary readable text color")

class Typography(BaseModel):
    heading_font: str = Field(default="Calibri", description="Font used for titles and headers")
    body_font: str = Field(default="Calibri", description="Font used for paragraphs and tables")
    heading_sizes: Dict[str, int] = Field(
        default_factory=lambda: {"title": 26, "h1": 20, "h2": 15, "h3": 12, "body": 11}
    )

class LayoutRules(BaseModel):
    slide_layouts_available: List[str] = Field(
        default_factory=lambda: ["Title", "Title and Content", "Two Content", "Section Header"]
    )
    max_bullets_per_slide: int = Field(default=5, description="Maximum bullet points per slide")
    table_header_shading_hex: str = Field(default="#1B365D", description="Table header background fill")
    table_zebra_shading_hex: str = Field(default="#F4F7FA", description="Alternating row background fill")
    callout_box_style: str = Field(default="left_accent_border", description="Style of blockquote callouts")

class TemplateGuidanceProfile(BaseModel):
    template_type: Literal["PPTX", "DOCX", "RESEARCH_PAPER", "DEFAULT"] = "DEFAULT"
    source_file_name: Optional[str] = None
    source_file_path: Optional[str] = Field(default=None, description="Uploaded template on disk; builders reuse its layouts when possible")
    color_palette: ColorPalette = Field(default_factory=ColorPalette)
    typography: Typography = Field(default_factory=Typography)
    layout_rules: LayoutRules = Field(default_factory=LayoutRules)
    detected_section_hierarchy: Optional[List[str]] = Field(default_factory=list)

class DocumentControlMetadata(BaseModel):
    document_title: str = "Technical Specification & Architecture"
    file_name: str = "Deliverable_v1.0"
    version: str = "1.0"
    date: str = Field(default_factory=lambda: datetime.date.today().strftime("%d %B %Y"))
    author: str = "Prepared with AGENT-101 (AI-generated, human-reviewed)"
    language: str = "English"  # labels on cover/control pages are rendered in this language

class DocumentCompileRequest(BaseModel):
    topic_id: str
    title: str
    target_format: Literal["PPT", "DOCX", "MD", "PDF"]
    refined_content_markdown: str
    template_guidance: Optional[TemplateGuidanceProfile] = Field(default_factory=TemplateGuidanceProfile)
    document_control_metadata: Optional[DocumentControlMetadata] = Field(default_factory=DocumentControlMetadata)
    output_directory: Optional[str] = "storage/outputs"
    display_title: Optional[str] = Field(default=None, description="Title shown in the document (e.g. translated); file names use `title`")
    speaker_notes: Optional[Dict[str, str]] = Field(default=None, description="Presenter notes keyed by section heading (decks only)")

class AccessibilityReport(BaseModel):
    wcag_compliant: bool = True
    contrast_ratio: float = 7.5
    heading_order_valid: bool = True
    table_headers_tagged: bool = True
    details: List[str] = Field(default_factory=list)

class DocumentCompileResult(BaseModel):
    success: bool
    file_path: str
    file_name: str
    format: str
    file_size_bytes: int = 0
    page_or_slide_count: int = 0
    wcag_compliant: bool = True
    accessibility_report: Optional[AccessibilityReport] = None
    error_message: Optional[str] = None
