import re
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

    def run(self, plan: ContentPlan, knowledge: KnowledgePackage, template_guidance: Optional[Dict[str, Any]] = None,
            requirements: Optional[Dict[str, Any]] = None, user_instructions: Optional[str] = None,
            language: str = "English") -> str:
        guidance_str = ""
        if template_guidance:
            guidance_str = (
                f"Template Type: {template_guidance.get('template_type', 'DOCX')}\n"
                f"Typography: {template_guidance.get('typography', {}).get('heading_font', 'Calibri')}\n"
                f"Max Bullets: {template_guidance.get('layout_rules', {}).get('max_bullets_per_slide', 5)}"
            )

        facts_str = "\n".join([f"- {f.fact} [{f.citation}]" for f in knowledge.key_facts])

        reqs = requirements or {}
        prompt = (
            f"Document Title: {plan.title}\n"
            f"Target Format: {plan.target_format}\n"
            f"Objective: {reqs.get('objective', '')}\n"
            f"Audience: {reqs.get('target_audience', '')}\n"
            f"Tone: {reqs.get('tone', '')}\n"
            f"User Instructions: {user_instructions or 'None'}\n"
            f"Language: write the entire document in {language} (keep source names as published).\n"
            + ("Sources (STRICT): the Grounded Facts below come from the user's own documents and are the ONLY "
               "allowed source of facts. Do not add any benefit, number, name, date or claim that is not in them. "
               "Cite every sentence that states a fact with its exact label in square brackets, e.g. [report.pdf, p.3]. "
               "If a planned section has no supporting facts, write at most one general sentence for it or omit it.\n"
               if knowledge.from_user_sources else "") +
            f"Template Guidance:\n{guidance_str}\n"
            f"Grounded Facts:\n{facts_str}\n\n"
            f"Sections to Write:\n" + "\n".join([
                f"- {s.heading} (~{s.target_word_count} words). Cover: {'; '.join(s.key_points)}" for s in plan.sections
            ]) + "\n\n"
            "Generate the complete markdown document now: start with '# ' and the title, use '## ' for each section, "
            "include at least one markdown table with a header row, and cite facts inline as [Source]. "
            "Do not include word counts, format or font notes, or any other meta commentary. Output only the markdown."
        )

        draft_content = llm_service.generate_completion(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, response_format="text")

        # Strip planning annotations such as "(≈ 200 words)" if the model echoes them into headings.
        draft_content = re.sub(r"\s*\*?\((?:≈|~|approx\.?)?\s*\d+\s*words?\)\*?", "", draft_content)

        # Some models cite with lenticular brackets; normalise to [ ] so citations can be checked.
        draft_content = draft_content.replace("【", "[").replace("】", "]")

        # Clean formatting
        if not draft_content.startswith("# "):
            draft_content = f"# {plan.title}\n\n" + draft_content

        return draft_content

generation_agent = GenerationAgent()
