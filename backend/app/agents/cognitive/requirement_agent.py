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

    def run(self, title: str, description: str, user_instructions: Optional[str] = None) -> StructuredRequirements:
        prompt = (
            f"Topic/Title: {title}\n"
            f"Description: {description}\n"
            f"Additional User Instructions: {user_instructions or 'None'}\n\n"
            "Analyze audience persona, extract core objectives, list key deliverables, and flag constraints."
        )

        data = llm_service.generate_json(prompt=prompt, system_prompt=self.SYSTEM_PROMPT)
        
        try:
            return StructuredRequirements(**data)
        except Exception:
            return StructuredRequirements(
                objective=data.get("objective", f"Develop a comprehensive report on '{title}'."),
                target_audience=data.get("target_audience", "Domain professionals and decision makers."),
                key_deliverables=data.get("key_deliverables", [title, "Technical Outline", "Implementation Guide"]),
                tone=data.get("tone", "Professional, analytical, and authoritative"),
                constraints=data.get("constraints", ["Grade 8-10 readability", "Active voice", "Zero cross-topic leaks"])
            )

requirement_agent = RequirementAgent()
