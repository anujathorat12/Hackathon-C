import hashlib
from typing import Dict
from app.agents.cognitive.revision_agent import split_sections
from app.services.llm_service import llm_service


class SpeakerNotesAgent:
    """
    Writes presenter talking points for each slide section of a deck.
    Results are cached per section text, so edits only regenerate the sections that changed.
    """

    SYSTEM_PROMPT = (
        "You are the Speaker Notes Agent. For each slide section you receive, write what a confident presenter "
        "would say aloud: 2-4 natural, conversational sentences that explain and connect the points, and a short "
        "transition where it helps. Do not repeat the bullets word for word, do not invent statistics or sources, "
        "and write in the same language as the slides. Return a JSON object mapping each exact section heading "
        "to its notes string."
    )

    @staticmethod
    def _key(heading: str, text: str) -> str:
        return hashlib.sha1(f"{heading}\n{text}".encode("utf-8")).hexdigest()

    def notes_for(self, markdown: str, cache: Dict[str, str]) -> Dict[str, str]:
        """Return {section heading: notes}; uses and fills `cache` (keyed by section content hash)."""
        _, sections = split_sections(markdown)
        missing = [(h, t) for h, t in sections if self._key(h, t) not in cache]
        if missing:
            prompt = "Write speaker notes for these slide sections:\n\n" + "\n\n".join(t.strip() for _, t in missing)
            fallbacks_before = llm_service.fallback_count
            data = llm_service.generate_json(prompt=prompt, system_prompt=self.SYSTEM_PROMPT)
            if llm_service.fallback_count == fallbacks_before and isinstance(data, dict):
                for heading, text in missing:
                    note = data.get(heading) or data.get(heading.strip("# ").strip())
                    if isinstance(note, str) and note.strip():
                        cache[self._key(heading, text)] = note.strip()
        return {h: cache[self._key(h, t)] for h, t in sections if self._key(h, t) in cache}


notes_agent = SpeakerNotesAgent()
