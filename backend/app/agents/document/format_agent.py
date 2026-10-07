import os
import re
from typing import Optional
from ...shared.schemas.template_models import (
    DocumentCompileRequest,
    DocumentCompileResult,
    DocumentControlMetadata,
    TemplateGuidanceProfile
)
from ...converters.docx.docx_builder import build_docx_deliverable
from ...converters.pptx.pptx_builder import build_pptx_deliverable
from ...converters.pdf_md.pdf_builder import build_pdf_deliverable
from ...converters.pdf_md.md_builder import build_md_deliverable
from .wcag_validator import audit_accessibility

class FormatGenerationAgent:
    """
    Agent 7: Format Generation Agent
    The central binary document factory that turns refined markdown into native
    PowerPoint (.pptx), Word (.docx), PDF (.pdf), or clean Markdown (.md) files.
    """

    def __init__(self, agent_name: str = "Format Generation Agent"):
        self.agent_name = agent_name

    def clean_filename(self, title: str) -> str:
        """Sanitizes document title into an enterprise standard filename."""
        clean = re.sub(r'[^a-zA-Z0-9]', '', title.title())
        return clean[:30] if clean else "Deliverable"

    def compile_document(self, request: DocumentCompileRequest) -> DocumentCompileResult:
        """
        Main execution method for Agent 7.
        Dispatches to the appropriate native compiler based on target_format.
        """
        fmt = request.target_format.upper()
        clean_title = self.clean_filename(request.title)
        
        ext_map = {
            "DOCX": "docx",
            "PPT": "pptx",
            "PDF": "pdf",
            "MD": "md"
        }
        file_ext = ext_map.get(fmt, "docx")
        version = (request.document_control_metadata.version if request.document_control_metadata else None) or "1.0"
        file_name = f"{clean_title}_v{version}.{file_ext}"

        output_dir = request.output_directory or "storage/outputs"
        os.makedirs(output_dir, exist_ok=True)
        target_path = os.path.join(output_dir, file_name)

        print(f"[{self.agent_name}] Compiling native deliverable: {file_name} (Format: {fmt})")

        # 1. Prepare Document Control Metadata
        metadata = request.document_control_metadata or DocumentControlMetadata()
        metadata.document_title = request.title
        metadata.file_name = file_name

        guidance = request.template_guidance or TemplateGuidanceProfile()

        # 2. Audit Accessibility (WCAG 2.2 AA)
        access_report = audit_accessibility(request.refined_content_markdown, guidance)

        try:
            # 3. Route to Native Binary Builder
            if fmt == "DOCX":
                out_file = build_docx_deliverable(
                    request.refined_content_markdown,
                    target_path,
                    metadata=metadata,
                    guidance=guidance
                )
            elif fmt == "PPT":
                out_file = build_pptx_deliverable(
                    request.refined_content_markdown,
                    target_path,
                    metadata=metadata,
                    guidance=guidance,
                    speaker_notes=request.speaker_notes
                )
            elif fmt == "PDF":
                out_file = build_pdf_deliverable(
                    request.refined_content_markdown,
                    target_path,
                    metadata=metadata,
                    guidance=guidance
                )
            elif fmt == "MD":
                out_file = build_md_deliverable(
                    request.refined_content_markdown,
                    target_path,
                    metadata=metadata
                )
            else:
                raise ValueError(f"Unsupported deliverable format: {fmt}")

            # 4. Measure Output File Metrics
            file_size = os.path.getsize(out_file) if os.path.exists(out_file) else 0
            
            # Estimate slide/page count
            page_count = 1
            if fmt == "PPT":
                page_count = len(request.refined_content_markdown.split("<!-- slide -->"))
            elif fmt in ["DOCX", "PDF"]:
                word_count = len(request.refined_content_markdown.split())
                page_count = max(2, (word_count // 350) + 1) # ~350 words per page + cover

            print(f"[{self.agent_name}] Compilation successful! File size: {file_size} bytes. WCAG: {access_report.wcag_compliant}")

            return DocumentCompileResult(
                success=True,
                file_path=os.path.abspath(out_file),
                file_name=file_name,
                format=fmt,
                file_size_bytes=file_size,
                page_or_slide_count=page_count,
                wcag_compliant=access_report.wcag_compliant,
                accessibility_report=access_report,
                error_message=None
            )
        except Exception as e:
            print(f"[{self.agent_name}] Error compiling {fmt} deliverable: {e}")
            return DocumentCompileResult(
                success=False,
                file_path="",
                file_name=file_name,
                format=fmt,
                file_size_bytes=0,
                page_or_slide_count=0,
                wcag_compliant=False,
                accessibility_report=access_report,
                error_message=str(e)
            )
