from typing import Dict, Any, Optional
from app.agents.cognitive.planning_agent import ContentPlan
from app.agents.cognitive.research_agent import KnowledgePackage
from app.services.llm_service import llm_service

class GenerationAgent:
    """
    Agent 5: Content Generation Agent
    Writes complete section-by-section draft markdown text following style rules and template guidance.
    Rules:
    - Active voice and direct phrasing.
    - Action verbs (Identify, Synthesize, Compare, Draft, Structure).
    - Structured markdown tables with header rows.
    - Max 5 bullets per slide/section if PPT layout.
    """

    SYSTEM_PROMPT = (
        "You are the Content Generation Agent (Agent 5). "
        "Write full structured markdown content section by section based on the content plan, research, and template guidance. "
        "Strictly adhere to writing style rules: use active voice, observable action verbs (Identify, Synthesize, Compare, Draft, Structure), "
        "and include markdown tables with header rows. Limit bullet points to maximum 5 per block."
    )

    def run(self, plan: ContentPlan, knowledge: KnowledgePackage, template_guidance: Optional[Dict[str, Any]] = None) -> str:
        guidance_str = ""
        if template_guidance:
            guidance_str = (
                f"Template Type: {template_guidance.get('template_type', 'DOCX')}\n"
                f"Typography: {template_guidance.get('typography', {}).get('heading_font', 'Calibri')}\n"
                f"Max Bullets: {template_guidance.get('layout_rules', {}).get('max_bullets_per_slide', 5)}"
            )

        facts_str = "\n".join([f"- {f.fact} [{f.citation}]" for f in knowledge.key_facts])

        prompt = (
            f"Document Title: {plan.title}\n"
            f"Target Format: {plan.target_format}\n"
            f"Template Guidance:\n{guidance_str}\n"
            f"Grounded Facts:\n{facts_str}\n\n"
            f"Sections to Write:\n" + "\n".join([f"- {s.section_id}: {s.heading} (Word count ~{s.target_word_count})" for s in plan.sections]) + "\n\n"
            "Generate the complete markdown text now. Include tables and structured headers."
        )

        draft_content = llm_service.generate_completion(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, response_format="text")
        
        # Clean formatting
        if not draft_content.startswith("# "):
            draft_content = f"# {plan.title}\n\n" + draft_content

        return draft_content

generation_agent = GenerationAgent()
