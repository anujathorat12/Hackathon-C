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

    def run(self, title: str, target_format: str, requirements: StructuredRequirements) -> ContentPlan:
        prompt = (
            f"Document Title: {title}\n"
            f"Target Format: {target_format}\n"
            f"Objective: {requirements.objective}\n"
            f"Target Audience: {requirements.target_audience}\n"
            f"Deliverables: {', '.join(requirements.key_deliverables)}\n\n"
            f"Generate a multi-section document plan customized for {target_format} format."
        )
        data = llm_service.generate_json(prompt=prompt, system_prompt=self.SYSTEM_PROMPT)
        if isinstance(data, dict):
            data["target_format"] = target_format
        try:
            return ContentPlan(**data)
        except Exception:
            raw_sections = data.get("sections", [])
            sections = []
            for idx, s in enumerate(raw_sections, 1):
                sections.append(SectionPlan(
                    section_id=s.get("section_id", f"S{idx}"),
                    heading=s.get("heading", f"Section {idx}"),
                    key_points=s.get("key_points", ["Key point 1", "Key point 2"]),
                    target_word_count=s.get("target_word_count", 300),
                    layout_type=s.get("layout_type", "Standard Section")
                ))

            if not sections:
                sections = [
                    SectionPlan(section_id="S1", heading="1. Executive Summary", key_points=["System Overview", "Objectives"], target_word_count=300),
                    SectionPlan(section_id="S2", heading="2. Technical Architecture", key_points=["Core Components", "Workflow Integration"], target_word_count=450),
                    SectionPlan(section_id="S3", heading="3. Implementation & Validation", key_points=["Deployment Strategy", "Verification Results"], target_word_count=350)
                ]

            return ContentPlan(
                title=data.get("title", title),
                target_format=target_format,
                sections=sections
            )

planning_agent = PlanningAgent()
