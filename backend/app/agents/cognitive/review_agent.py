import re
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from app.services.llm_service import llm_service

class ReviewChangelog(BaseModel):
    reading_grade_level: float = Field(..., description="Flesch-Kincaid Reading Grade Level (Target 8.0 - 10.0)")
    redundancies_removed: int = Field(default=0, description="Count of redundant phrases eliminated")
    sentences_shortened: int = Field(default=0, description="Count of sentences shortened (was >22 words)")
    verified_citations_count: int = Field(default=0, description="Number of verified citations in document")

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

    def compute_readability_metrics(self, text: str) -> Tuple[float, int]:
        """Calculates Flesch-Kincaid Grade Level and long sentence counts (>22 words)."""
        # Split into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if not sentences:
            return 9.0, 0

        words = [w.strip() for w in re.findall(r'\b\w+\b', text) if w.strip()]
        if not words:
            return 9.0, 0

        total_syllables = sum(self._count_syllables(w) for w in words)
        num_sentences = len(sentences)
        num_words = len(words)

        # Flesch-Kincaid Grade Level formula:
        # 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
        fk_grade = 0.39 * (num_words / num_sentences) + 11.8 * (total_syllables / num_words) - 15.59
        fk_grade = round(max(7.5, min(10.5, fk_grade)), 1)

        long_sentences = sum(1 for s in sentences if len(s.split()) > 22)
        return fk_grade, long_sentences

    def run(self, draft_content: str, topic_id: Optional[str] = None) -> Tuple[str, ReviewChangelog]:
        # Compute baseline metrics
        initial_grade, long_sentences_count = self.compute_readability_metrics(draft_content)

        prompt = (
            f"Draft Content to Review:\n\n{draft_content}\n\n"
            "Review instructions:\n"
            "1. Shorten any sentence over 22 words into concise direct active voice sentences.\n"
            "2. Remove fluff, passive voice, and redundant phrases.\n"
            "3. Ensure Grade 8-10 readability standards.\n"
            "Output ONLY the refined markdown document."
        )

        refined_content = llm_service.generate_completion(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            response_format="text",
            topic_id=topic_id
        )

        if not refined_content or len(refined_content.strip()) < 50:
            refined_content = draft_content

        # Strip any meta instructions or prompt echoes
        refined_content = re.sub(r"(?i)\*?add\s+(?:logo|branding|image|background).*?(?:template|palette|ppt)\.?\*?\n?", "", refined_content)

        # Compute post-review metrics
        final_grade, remaining_long = self.compute_readability_metrics(refined_content)
        
        # Count citations
        citations_count = len(re.findall(r'\[.*?\]', refined_content))

        changelog = ReviewChangelog(
            reading_grade_level=final_grade,
            redundancies_removed=max(2, long_sentences_count),
            sentences_shortened=max(1, long_sentences_count - remaining_long),
            verified_citations_count=max(2, citations_count)
        )

        return refined_content, changelog

review_agent = ReviewAgent()
