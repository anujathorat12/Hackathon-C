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
            topic_id: Optional[str] = None) -> str:
        guidance_str = ""
        if template_guidance:
            sections = template_guidance.get("detected_section_hierarchy") or []
            palette = template_guidance.get("color_palette") or {}
            guidance_str = (
                f"Reference Template: {template_guidance.get('source_file_name', 'Corporate Presentation Template')}\n"
                f"Template Type: {template_guidance.get('template_type', 'DOCX')}\n"
                f"Reference Structure/Themes: {', '.join(sections) if sections else 'Standard corporate flow'}\n"
                f"Brand Palette: Primary {palette.get('primary_hex', '')}, Accent {palette.get('accent_hex', '')}, Secondary {palette.get('secondary_hex', '')}\n"
                f"Typography: {template_guidance.get('typography', {}).get('heading_font', 'Calibri')}\n"
                f"Max Bullets: {template_guidance.get('layout_rules', {}).get('max_bullets_per_slide', 5)}\n"
                "CRITICAL: Maintain the corporate template context, concise rhythm, and executive tone across EVERY slide (from Slide 1 to the end). "
                "Do NOT drop the template context after the first slide. Do NOT output placeholders like '*Add logo from reference PPT*' or meta notes."
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
            f"Template Guidance:\n{guidance_str}\n"
            f"Grounded Facts:\n{facts_str}\n\n"
            f"Sections to Write:\n" + "\n".join([
                f"- {s.heading} (~{s.target_word_count} words). Cover: {'; '.join(s.key_points)}" for s in plan.sections
            ]) + "\n\n"
            "Generate the complete markdown document now: start with '# ' and the title, use '## ' for each section/slide, "
            "include at least one markdown table with a header row, and cite facts inline as [Source]. "
            "Every slide must have full, substantive bullet points and takeaways. "
            "Never output meta instructions or prompt echoes (such as '*Add logo/branding...*' or '*use same color palette*'). "
            "Output only the final clean markdown."
        )

        draft_content = llm_service.generate_completion(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            response_format="text",
            topic_id=topic_id
        )

        # Strip planning annotations such as "(≈ 200 words)" if the model echoes them into headings.
        draft_content = re.sub(r"\s*\*?\((?:≈|~|approx\.?)?\s*\d+\s*words?\)\*?", "", draft_content)

        # Strip common meta placeholders like "*Add logo/branding from the reference PPT...*"
        draft_content = re.sub(r"(?i)\*?add\s+(?:logo|branding|image|background).*?(?:template|palette|ppt)\.?\*?\n?", "", draft_content)

        # Clean formatting
        if not draft_content.startswith("# "):
            draft_content = f"# {plan.title}\n\n" + draft_content

        return draft_content

generation_agent = GenerationAgent()
