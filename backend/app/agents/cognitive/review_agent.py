import re
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field
from app.services.llm_service import llm_service

CITATION_NEEDS_SPACE = re.compile(r"(?<=[^\s\[(!])\[(?=[^\]\n]{2,150}\](?!\())")


def tidy_citations(text: str) -> str:
    """Normalise citation brackets (some models use 【】) and keep a space before each [citation]."""
    text = text.replace("【", "[").replace("】", "]")
    return CITATION_NEEDS_SPACE.sub(" [", text)


class ReviewChangelog(BaseModel):
    # All values are measured on the actual draft and refined text; none are estimated or padded.
    reading_grade_level: float = Field(..., description="Flesch-Kincaid grade of the refined prose (target 8-10)")
    initial_reading_grade_level: float = Field(default=0.0, description="Flesch-Kincaid grade of the draft prose")
    words_trimmed: int = Field(default=0, description="Words removed by the review (draft words - refined words, min 0)")
    sentences_shortened: int = Field(default=0, description="Reduction in sentences over 22 words")
    long_sentences_remaining: int = Field(default=0, description="Sentences still over 22 words after review")
    citations_count: int = Field(default=0, description="Distinct inline [Source] citations in the refined text")

class ReviewAgent:
    """
    Agent 6: Content Review Agent
    Audits draft content against quality metrics:
    - Flesch-Kincaid Readability (Grade 8-10 target).
    - Sentence length audit (flags and shortens sentences > 22 words).
    - Tone check and redundancy removal.
    - Emits RefinedContent string and ReviewChangelog object.
    """

    SYSTEM_PROMPT = (
        "You are the Content Review Agent (Agent 6). "
        "Audit and refine draft content to ensure active voice, professional objective tone, "
        "Grade 8-10 readability, and sentence lengths under 22 words. "
        "Remove redundancies and return the refined markdown content."
    )

    def _count_syllables(self, word: str) -> int:
        word = word.lower()
        if len(word) <= 3:
            return 1
        word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
        word = re.sub(r'^y', '', word)
        syllables = len(re.findall(r'[aeiouy]{1,2}', word))
        return max(1, syllables)

    @staticmethod
    def _prose(text: str) -> str:
        """Readable prose only: drops tables, code and markdown syntax; each heading/bullet ends a sentence."""
        lines = []
        in_code = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code or not stripped or stripped.startswith("|") or re.fullmatch(r"[-*_=\s]{3,}", stripped):
                continue
            stripped = re.sub(r"^(#{1,6}|[-*+]|\d+[.)])\s+", "", stripped)          # heading / bullet markers
            stripped = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", stripped)           # links -> text
            stripped = re.sub(r"\[[^\]]*\]", "", stripped)                          # inline citations
            stripped = re.sub(r"[*_`>]", "", stripped).strip()
            if stripped:
                lines.append(stripped if stripped[-1] in ".!?:" else stripped + ".")
        return " ".join(lines)

    def compute_readability_metrics(self, text: str) -> Tuple[float, int]:
        """Flesch-Kincaid grade level of the prose and the number of sentences over 22 words."""
        prose = self._prose(text)
        sentences = [s.strip() for s in re.split(r"[.!?:]+", prose) if s.strip()]
        words = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", prose)
        if not sentences or not words:
            return 0.0, 0

        total_syllables = sum(self._count_syllables(w) for w in words)
        # Flesch-Kincaid: 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
        fk_grade = 0.39 * (len(words) / len(sentences)) + 11.8 * (total_syllables / len(words)) - 15.59
        long_sentences = sum(1 for s in sentences if len(s.split()) > 22)
        return round(max(0.0, fk_grade), 1), long_sentences

    @staticmethod
    def count_citations(text: str) -> int:
        """Distinct inline citations: [IPCC, 2023] or (ICAR, 2022). Ignores markdown links and task-list boxes."""
        bracketed = re.findall(r"\[([^\]\n]{2,150})\](?!\()", text)
        author_year = re.findall(r"\(([^()\n]{2,100}?,?\s(?:19|20)\d{2}[a-z]?)\)", text)
        return len({c.strip().lower() for c in bracketed + author_year if c.strip().lower() not in ("x", " ")})

    @staticmethod
    def count_words(text: str) -> int:
        return len(re.findall(r"\b\w+\b", text))

    def run(self, draft_content: str, language: str = "English") -> Tuple[str, ReviewChangelog]:
        # Flesch-Kincaid is only defined for English; other languages report 0 (shown as n/a).
        english = language.lower().startswith("english")
        initial_grade, long_sentences_count = self.compute_readability_metrics(draft_content)

        prompt = (
            f"Draft Content to Review:\n\n{draft_content}\n\n"
            "Review instructions:\n"
            "1. Shorten any sentence over 22 words into concise direct active voice sentences.\n"
            "2. Remove fluff, passive voice, and redundant phrases.\n"
            "3. Ensure Grade 8-10 readability standards.\n"
            "4. Keep every inline source citation (e.g. [IPCC, 2023]) attached to the fact it supports; never drop or invent citations.\n"
            "5. Keep all headings, tables and the overall structure.\n"
            f"6. Keep the document in {language}.\n"
            "Output ONLY the refined markdown document."
        )

        refined_content = llm_service.generate_completion(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, response_format="text")

        if not refined_content or len(refined_content.strip()) < 50:
            refined_content = draft_content
        refined_content = tidy_citations(refined_content)

        # Measure the refined text against the draft.
        final_grade, remaining_long = self.compute_readability_metrics(refined_content)

        changelog = ReviewChangelog(
            reading_grade_level=final_grade if english else 0.0,
            initial_reading_grade_level=initial_grade if english else 0.0,
            words_trimmed=max(0, self.count_words(draft_content) - self.count_words(refined_content)),
            sentences_shortened=max(0, long_sentences_count - remaining_long),
            long_sentences_remaining=remaining_long,
            citations_count=self.count_citations(refined_content),
        )

        return refined_content, changelog

review_agent = ReviewAgent()
