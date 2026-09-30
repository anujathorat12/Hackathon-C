import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.agents.document.reference_agent import ReferenceAnalysisAgent
from backend.app.agents.document.format_agent import FormatGenerationAgent
from backend.app.shared.schemas.template_models import (
    DocumentCompileRequest,
    DocumentControlMetadata,
    TemplateGuidanceProfile
)

def run_tests():
    print("==================================================================")
    print("RUNNING STANDALONE TEST HARNESS: MODULE C DOCUMENT COMPILERS")
    print("==================================================================")

    # 1. Load Fixtures
    fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "shared", "fixtures"))
    sample_md_path = os.path.join(fixture_dir, "sample_refined_content.md")
    
    if os.path.exists(sample_md_path):
        with open(sample_md_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    else:
        markdown_content = """# Clinical Healthcare Multi-Agent Systems

## 1. Executive Summary
This architecture brief outlines the deployment of autonomous multi-agent systems for hospital emergency triage.

> **Operational Standard:** All clinical suggestions must remain non-diagnostic.

## 2. Core Architectural Pillars
* **Triage Intake Tier:** Ingests unstructured vitals and notes.
* **Clinical Knowledge Synthesis:** Grounded medical literature.

## 3. Performance & Safety Benchmarks
| Metric Category | Target Standard | Measured Performance | Compliance Status |
| :--- | :--- | :--- | :--- |
| Triage Latency | < 180 seconds | 142 seconds | Fully Compliant |
| Drug Recall | > 99.0% | 99.8% | Exceeds Target |

<!-- slide -->
# Clinical Multi-Agent Architecture
## Emergency Department Decision Support & Triage Synthesis

<!-- slide -->
# Clinical Safety & Triage Benchmarks
* **Triage Latency:** Completed in 142 seconds (Target: < 180s)
* **Drug Interaction Recall:** 99.8% precision across 1,200 scenarios
* **Physician Approval:** 92.4% clinical acceptance rate
* **WCAG 2.2 AA:** Accessible tables and 7.2:1 color contrast ratio
"""
    print(f"Loaded markdown fixture: {len(markdown_content)} characters.")

    # Reference docx in workspace
    sample_docx_template = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "AI_Hackathon", "AGENT-101_SystemBrief-StyleGuide_v1.0.docx"))

    # Output directory for test artifacts
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "outputs"))
    os.makedirs(output_dir, exist_ok=True)

    # ==================================================================
    # TEST 1: AGENT 3 - REFERENCE TEMPLATE ANALYSIS (DEFAULT FALLBACK)
    # ==================================================================
    print("\n--- TEST 1: Reference Analysis Agent (Default Theme) ---")
    ref_agent = ReferenceAnalysisAgent()
    default_guidance = ref_agent.analyze_template(None)
    assert default_guidance.template_type == "DEFAULT"
    assert default_guidance.color_palette.primary_hex == "#1B365D"
    print("Test 1 Passed: Default guidance successfully generated.")

    # ==================================================================
    # TEST 2: AGENT 3 - REFERENCE TEMPLATE ANALYSIS (REAL DOCX TEMPLATE)
    # ==================================================================
    print("\n--- TEST 2: Reference Analysis Agent (Real DOCX Ingestion) ---")
    if os.path.exists(sample_docx_template):
        extracted_guidance = ref_agent.analyze_template(sample_docx_template)
        assert extracted_guidance.template_type == "DOCX"
        print(f"Test 2 Passed: Ingested '{sample_docx_template}' -> Extracted Primary: {extracted_guidance.color_palette.primary_hex}, Font: {extracted_guidance.typography.heading_font}")
    else:
        print("Skipping Test 2: Sample docx template not found at path.")
        extracted_guidance = default_guidance

    # ==================================================================
    # TEST 3: AGENT 7 - COMPILE NATIVE WORD DOCUMENT (.DOCX)
    # ==================================================================
    print("\n--- TEST 3: Format Generation Agent -> DOCX Compilation ---")
    format_agent = FormatGenerationAgent()
    docx_req = DocumentCompileRequest(
        topic_id="test-topic-101",
        title="Clinical Healthcare Multi-Agent Systems",
        target_format="DOCX",
        refined_content_markdown=markdown_content,
        template_guidance=extracted_guidance,
        document_control_metadata=DocumentControlMetadata(
            document_title="Clinical Healthcare Multi-Agent Systems",
            file_name="ClinicalHealthcare_SystemDeliverable_v1.0.docx",
            version="1.0 (Final System Specification)",
            date="30 September 2026",
            author="Autonomous AI Multi-Agent Platform (AGENT-101)"
        ),
        output_directory=output_dir
    )
    docx_result = format_agent.compile_document(docx_req)
    assert docx_result.success is True
    assert os.path.exists(docx_result.file_path)
    assert docx_result.file_size_bytes > 0
    assert docx_result.wcag_compliant is True
    print(f"Test 3 Passed: Native DOCX generated at: {docx_result.file_path} ({docx_result.file_size_bytes} bytes)")

    # ==================================================================
    # TEST 4: AGENT 7 - COMPILE NATIVE PRESENTATION (.PPTX)
    # ==================================================================
    print("\n--- TEST 4: Format Generation Agent -> PPTX Compilation ---")
    pptx_req = DocumentCompileRequest(
        topic_id="test-topic-101",
        title="Clinical Multi-Agent Architecture",
        target_format="PPT",
        refined_content_markdown=markdown_content,
        template_guidance=extracted_guidance,
        document_control_metadata=DocumentControlMetadata(
            document_title="Clinical Multi-Agent Architecture",
            file_name="ClinicalMultiAgent_Presentation_v1.0.pptx",
            version="1.0 (Executive Pitch)",
            date="30 September 2026",
            author="Autonomous AI Multi-Agent Platform (AGENT-101)"
        ),
        output_directory=output_dir
    )
    pptx_result = format_agent.compile_document(pptx_req)
    assert pptx_result.success is True
    assert os.path.exists(pptx_result.file_path)
    assert pptx_result.file_size_bytes > 0
    print(f"Test 4 Passed: Native PPTX generated at: {pptx_result.file_path} ({pptx_result.file_size_bytes} bytes, {pptx_result.page_or_slide_count} slides)")

    # ==================================================================
    # TEST 5: AGENT 7 - COMPILE CLEAN MARKDOWN (.MD)
    # ==================================================================
    print("\n--- TEST 5: Format Generation Agent -> Markdown Compilation ---")
    md_req = DocumentCompileRequest(
        topic_id="test-topic-101",
        title="Clinical Healthcare Multi-Agent Systems",
        target_format="MD",
        refined_content_markdown=markdown_content,
        output_directory=output_dir
    )
    md_result = format_agent.compile_document(md_req)
    assert md_result.success is True
    assert os.path.exists(md_result.file_path)
    print(f"Test 5 Passed: Markdown exported at: {md_result.file_path}")

    # ==================================================================
    # TEST 6: AGENT 7 - COMPILE PDF DELIVERABLE (.PDF)
    # ==================================================================
    print("\n--- TEST 6: Format Generation Agent -> PDF Compilation ---")
    pdf_req = DocumentCompileRequest(
        topic_id="test-topic-101",
        title="Clinical Healthcare Multi-Agent Systems",
        target_format="PDF",
        refined_content_markdown=markdown_content,
        template_guidance=extracted_guidance,
        output_directory=output_dir
    )
    pdf_result = format_agent.compile_document(pdf_req)
    assert pdf_result.success is True
    assert os.path.exists(pdf_result.file_path)
    print(f"Test 6 Passed: PDF deliverable generated at: {pdf_result.file_path} ({pdf_result.file_size_bytes} bytes)")

    print("\n==================================================================")
    print("ALL TESTS PASSED! MODULE C COMPILATION ENGINE IS 100% OPERATIONAL.")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
