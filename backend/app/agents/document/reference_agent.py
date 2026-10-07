import os
from typing import Optional
from ...shared.schemas.template_models import TemplateGuidanceProfile
from ...parsers.docx_parser import parse_docx_template
from ...parsers.pptx_parser import parse_pptx_template
from ...parsers.pdf_parser import parse_pdf_template
from ...parsers.template_normalizer import normalize_guidance

class ReferenceAnalysisAgent:
    """
    Agent 3: Reference Analysis Agent
    Inspects user-uploaded template files (.pptx, .docx, .pdf, .md),
    extracts structural hierarchies, visual color schemes, and font styles,
    and returns a standardized TemplateGuidanceProfile.
    """

    def __init__(self, agent_name: str = "Reference Analysis Agent"):
        self.agent_name = agent_name

    def analyze_template(self, file_path: Optional[str] = None) -> TemplateGuidanceProfile:
        """
        Main entry point for Agent 3.
        If file_path is None or does not exist, returns enterprise default theme.
        Otherwise, routes to the appropriate format inspector.
        """
        if not file_path or not os.path.exists(file_path):
            print(f"[{self.agent_name}] No reference template uploaded. Applying default corporate theme.")
            return normalize_guidance()

        ext = os.path.splitext(file_path)[1].lower()
        print(f"[{self.agent_name}] Ingesting reference template: {file_path} (Format: {ext})")

        if ext == ".docx":
            profile = parse_docx_template(file_path)
        elif ext in [".pptx", ".ppt"]:
            profile = parse_pptx_template(file_path)
        elif ext == ".pdf":
            profile = parse_pdf_template(file_path)
        elif ext in [".md", ".markdown", ".txt"]:
            profile = normalize_guidance({
                "template_type": "DOCX",
                "source_file_name": os.path.basename(file_path)
            })
        else:
            print(f"[{self.agent_name}] Unsupported template extension '{ext}'. Falling back to default.")
            profile = normalize_guidance()

        profile.source_file_path = os.path.abspath(file_path)
        print(f"[{self.agent_name}] Successfully generated TemplateGuidanceProfile (Type: {profile.template_type}, Primary Color: {profile.color_palette.primary_hex})")
        return profile
