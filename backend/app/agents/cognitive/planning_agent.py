from typing import List, Optional
from pydantic import BaseModel, Field
from app.agents.cognitive.requirement_agent import StructuredRequirements
from app.services.llm_service import llm_service

class SectionPlan(BaseModel):
    section_id: str
    heading: str
    key_points: List[str]
    target_word_count: int = 300
    layout_type: str = "Standard Section"

class ContentPlan(BaseModel):
    title: str
    target_format: str
    sections: List[SectionPlan]

class PlanningAgent:
    """
    Agent 2: Planning Agent
    Generates hierarchical document outline tailored to target format (PPT, DOCX, MD, PDF).
    """

    SYSTEM_PROMPT = (
        "You are the Planning Agent (Agent 2). "
        "Create a detailed section-by-section outline tailored to the specified format (PPT, DOCX, MD, PDF). "
        "Output a JSON object with 'title', 'target_format', and an array of 'sections' containing: "
        "'section_id', 'heading', 'key_points', 'target_word_count', and 'layout_type'."
    )

    def run(self, title: str, target_format: str, requirements: StructuredRequirements,
            template_guidance: Optional[dict] = None, topic_id: Optional[str] = None) -> ContentPlan:
        template_context = ""
        if template_guidance:
            sections = template_guidance.get("detected_section_hierarchy") or []
            if sections:
                template_context = (
                    f"Reference Template Slide Structure:\n"
                    f"The template provides these slide themes/sections: {', '.join(sections)}.\n"
                    f"You MUST align your presentation outline with this corporate structure, adapting the topic '{title}' "
                    f"across each of these slide themes consistently.\n\n"
                )

        prompt = (
            f"Document Title: {title}\n"
            f"Target Format: {target_format}\n"
            f"Objective: {requirements.objective}\n"
            f"Target Audience: {requirements.target_audience}\n"
            f"Deliverables: {', '.join(requirements.key_deliverables)}\n"
            f"Tone: {requirements.tone}\n"
            f"Constraints: {', '.join(requirements.constraints)}\n\n"
            f"{template_context}"
            f"Generate a multi-section document plan customized for {target_format} format "
            f"({'5-8 slides, one section per slide' if target_format == 'PPT' else '4-7 sections'}). "
            "Ensure the template flow and narrative continuity are maintained across ALL slides, from start to finish. "
            "Every section must be specifically about the document title above."
        )
        data = llm_service.generate_json(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, topic_id=topic_id)
        if not isinstance(data, dict):
            data = {}

        # LLMs return loosely-typed JSON (e.g. numeric section_id), so normalise before validating.
        raw_sections = data.get("sections") or []
        sections = []
        for idx, s in enumerate(raw_sections, 1):
            if not isinstance(s, dict):
                s = {"heading": str(s)}
            key_points = s.get("key_points") or []
            if not isinstance(key_points, list):
                key_points = [key_points]
            try:
                word_count = int(s.get("target_word_count") or 300)
            except (TypeError, ValueError):
                word_count = 300
            sections.append(SectionPlan(
                section_id=str(s.get("section_id") or f"S{idx}"),
                heading=str(s.get("heading") or s.get("title") or f"Section {idx}"),
                key_points=[str(k) for k in key_points] or ["Key point 1", "Key point 2"],
                target_word_count=word_count,
                layout_type=str(s.get("layout_type") or "Standard Section"),
            ))
        if not sections:
            sections = [
                SectionPlan(section_id="S1", heading="1. Executive Summary", key_points=["System Overview", "Objectives"], target_word_count=300),
                SectionPlan(section_id="S2", heading="2. Technical Architecture", key_points=["Core Components", "Workflow Integration"], target_word_count=450),
                SectionPlan(section_id="S3", heading="3. Implementation & Validation", key_points=["Deployment Strategy", "Verification Results"], target_word_count=350)
            ]

        return ContentPlan(
            title=str(data.get("title") or title),
            target_format=target_format,
            sections=sections
        )

planning_agent = PlanningAgent()
