import re
from typing import List, Optional, Tuple
from app.services.llm_service import llm_service


def split_sections(markdown: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Split markdown into (preamble, [(heading line, full section text)]) on '## ' headings."""
    preamble, sections = "", []
    for part in re.split(r"(?m)^(?=## )", markdown):
        if part.startswith("## "):
            sections.append((part.splitlines()[0][3:].strip(), part))
        else:
            preamble += part
    return preamble, sections


class RevisionAgent:
    """
    Human-in-the-loop revision: rewrites the whole document, or just one section,
    following a plain-language instruction from the reviewer.
    """

    SYSTEM_PROMPT = (
        "You are the Revision Agent. Apply the reviewer's instruction to the given markdown precisely. "
        "Change only what the instruction asks for. Keep the markdown structure (headings, bullets, tables), "
        "keep every inline source citation such as [IPCC, 2023] attached to its fact, never invent new citations "
        "or statistics, and write in the same language as the original. Output ONLY the revised markdown."
    )

    def _rewrite(self, text: str, instruction: str, scope: str) -> str:
        prompt = (
            f"Reviewer instruction: {instruction}\n\n"
            f"Apply it to this {scope}:\n\n{text}\n\n"
            "Return the full revised markdown for this " + scope + " only."
        )
        revised = llm_service.generate_completion(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, response_format="text")
        revised = re.sub(r"^```(?:markdown|md)?\s*|\s*```$", "", (revised or "").strip())
        revised = revised.replace("【", "[").replace("】", "]")
        return revised

    def run(self, markdown: str, instruction: str, section: Optional[str] = None) -> Tuple[str, str]:
        """Returns (revised markdown, human-readable summary of what was revised)."""
        fallbacks_before = llm_service.fallback_count
        if section:
            preamble, sections = split_sections(markdown)
            match = next((s for s in sections if s[0] == section), None)
            if match is None:
                raise ValueError(f"Section '{section}' was not found in the document.")
            revised = self._rewrite(match[1].strip(), instruction, "section")
            if not revised.startswith("## "):
                revised = f"## {section}\n\n{revised}"
            new_markdown = preamble + "".join(
                (revised.rstrip() + "\n\n") if s is match else s[1] for s in sections
            )
            target = f"section “{section}”"
        else:
            new_markdown = self._rewrite(markdown, instruction, "document")
            target = "the whole document"

        if llm_service.fallback_count > fallbacks_before or len(new_markdown.strip()) < 20:
            raise RuntimeError("The AI could not revise the content right now. Please try again in a minute.")
        return new_markdown, f"Revised {target}: “{instruction}”"


revision_agent = RevisionAgent()
