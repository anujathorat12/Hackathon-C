from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.llm_service import llm_service

class StructuredRequirements(BaseModel):
    objective: str = Field(..., description="Core objective of the document")
    target_audience: str = Field(..., description="Target audience persona")
    key_deliverables: List[str] = Field(default_factory=list, description="Key deliverables")
    tone: str = Field(default="Professional", description="Tone of writing")
    constraints: List[str] = Field(default_factory=list, description="System constraints")

class RequirementAgent:
    """
    Agent 1: Requirement Analysis Agent
    Parses raw topic, description, and user instructions into structured requirements.
    """
    
    SYSTEM_PROMPT = (
        "You are the Requirement Analysis Agent (Agent 1). "
        "Analyze the provided topic, description, and instructions. "
        "Output a JSON object containing: 'objective', 'target_audience', 'key_deliverables', 'tone', and 'constraints'."
    )

    def run(self, title: str, description: str, user_instructions: Optional[str] = None, topic_id: Optional[str] = None) -> StructuredRequirements:
        prompt = (
            f"Topic/Title: {title}\n"
            f"Description: {description}\n"
            f"Additional User Instructions: {user_instructions or 'None'}\n\n"
            "Analyze audience persona, extract core objectives, list key deliverables, and flag constraints."
        )

        data = llm_service.generate_json(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, topic_id=topic_id)
        if not isinstance(data, dict):
            data = {}

        # LLMs vary the JSON shape (e.g. audience as a list), so coerce each field to its expected type.
        def as_text(value, default: str) -> str:
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value if v)
            elif isinstance(value, dict):
                value = "; ".join(f"{k}: {v}" for k, v in value.items())
            return str(value).strip() if value else default

        def as_list(value, default: List[str]) -> List[str]:
            if isinstance(value, str):
                value = [value]
            elif isinstance(value, dict):
                value = [f"{k}: {v}" for k, v in value.items()]
            items = [str(v) if not isinstance(v, dict) else "; ".join(f"{k}: {x}" for k, x in v.items()) for v in (value or []) if v]
            return items or default

        return StructuredRequirements(
            objective=as_text(data.get("objective"), f"Develop a comprehensive report on '{title}'."),
            target_audience=as_text(data.get("target_audience"), "Domain professionals and decision makers."),
            key_deliverables=as_list(data.get("key_deliverables"), [title, "Technical Outline", "Implementation Guide"]),
            tone=as_text(data.get("tone"), "Professional, analytical, and authoritative"),
            constraints=as_list(data.get("constraints"), ["Grade 8-10 readability", "Active voice", "Zero cross-topic leaks"]),
        )

requirement_agent = RequirementAgent()
