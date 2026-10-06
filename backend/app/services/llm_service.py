import os
import json
import re
from typing import Dict, Any, Optional
from app.config import settings

class LLMService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.LLM_MODEL
        self.client = None
        # Incremented whenever a call is answered by the offline fallback instead of the LLM.
        self.fallback_count = 0
        
        if self.api_key:
            try:
                # Initialize OpenAI compatible client pointing to Groq API
                from openai import OpenAI
                # Bounded timeout so a stalled call can't freeze the pipeline; retries back off on 429 rate limits.
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=settings.GROQ_BASE_URL,
                    timeout=120,
                    max_retries=4
                )
            except Exception as e:
                print(f"[LLMService Warning] Could not initialize Groq/OpenAI client: {e}")

    def generate_completion(self, prompt: str, system_prompt: str, response_format: str = "text") -> str:
        """
        Generates completion using Groq API model (default 'gpt-oss-120b').
        Falls back to rule-based fallback generator if API key is not present.
        """
        if self.client:
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3
                }
                
                if response_format == "json":
                    kwargs["response_format"] = {"type": "json_object"}

                # gpt-oss models spend tokens on hidden reasoning; "low" keeps runs fast and within free-tier limits.
                if "gpt-oss" in self.model:
                    kwargs["extra_body"] = {"reasoning_effort": "low"}

                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if content:
                    return content
                print("[LLMService Error] Groq returned an empty response. Falling back to cognitive parser.", flush=True)
            except Exception as e:
                print(f"[LLMService Error] Groq API call failed ({e}). Falling back to cognitive parser.", flush=True)
        
        self.fallback_count += 1
        return self._generate_fallback(prompt, system_prompt, response_format)

    def generate_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Generates and parses structured JSON output with automatic JSON cleanup.
        """
        raw_output = self.generate_completion(prompt, system_prompt, response_format="json")
        
        # Clean JSON markdown codeblocks if present
        clean_output = raw_output.strip()
        if clean_output.startswith("```json"):
            clean_output = clean_output[7:]
        if clean_output.startswith("```"):
            clean_output = clean_output[3:]
        if clean_output.endswith("```"):
            clean_output = clean_output[:-3]
        clean_output = clean_output.strip()
        
        try:
            return json.loads(clean_output)
        except json.JSONDecodeError:
            # Fallback JSON extraction via regex
            match = re.search(r'(\{.*\}|\[.*\])', clean_output, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return {"error": "Failed to parse JSON response", "raw": raw_output}

    def _generate_fallback(self, prompt: str, system_prompt: str, response_format: str) -> str:
        """Deterministic mock fallback when API key is missing or offline."""
        if response_format == "json":
            if "Requirement Analysis Agent" in system_prompt or "StructuredRequirements" in prompt:
                return json.dumps({
                    "objective": "Design and document an enterprise-grade multi-agent autonomous framework.",
                    "target_audience": "Enterprise software architects, engineering leads, and domain specialists.",
                    "key_deliverables": ["System Architecture Specification", "Pipeline Flow Diagram", "Data Models"],
                    "tone": "Professional, analytical, and authoritative",
                    "constraints": ["Grade 8-10 readability", "Active voice", "Zero cross-topic context leaks"]
                })
            elif "Planning Agent" in system_prompt or "ContentPlan" in prompt:
                return json.dumps({
                    "title": "Autonomous Multi-Agent AI System Architecture",
                    "target_format": "DOCX",
                    "sections": [
                        {
                            "section_id": "S1",
                            "heading": "1. Executive Summary & Strategic Objectives",
                            "key_points": ["System overview", "Core architectural pillars", "Value proposition"],
                            "target_word_count": 300,
                            "layout_type": "Standard Section"
                        },
                        {
                            "section_id": "S2",
                            "heading": "2. Multi-Agent Orchestration & Cognitive Workflow",
                            "key_points": ["State machine topology", "Agent roles and contracts", "Telemetry events"],
                            "target_word_count": 450,
                            "layout_type": "Technical Section"
                        },
                        {
                            "section_id": "S3",
                            "heading": "3. Context Isolation & Security Architecture",
                            "key_points": ["Topic-scoped vector retrieval", "Session cache isolation", "Data compliance"],
                            "target_word_count": 350,
                            "layout_type": "Security Section"
                        }
                    ]
                })
            elif "Research" in system_prompt or "KnowledgePackage" in prompt:
                return json.dumps({
                    "topic_id": "global_knowledge",
                    "key_facts": [
                        {"fact": "LangGraph enables stateful graph orchestration for multi-agent workflows.", "citation": "LangGraph Docs 2026"},
                        {"fact": "MongoDB Atlas Vector Search allows topic-scoped filtering via $vectorSearch pipelines.", "citation": "MongoDB Spec 2026"}
                    ],
                    "grounded_references": ["LangGraph Stateful Graph Guide", "MongoDB Atlas Vector Indexing Specs"],
                    "domain_context": "Enterprise AI systems require strict state boundaries, deterministic audit trails, and zero hallucination policies."
                })
            else:
                return json.dumps({"status": "completed", "details": "Processed standard fallback payload"})
        else:
            return (
                "# Autonomous Multi-Agent AI System Architecture\n\n"
                "## 1. Executive Summary & Strategic Objectives\n"
                "The Multi-Agent AI Content Generation System converts user prompts into publication-ready documents. "
                "The engine isolates workspace context per topic ID to prevent memory leaks across sessions.\n\n"
                "| Component | Tech Stack | Role |\n"
                "|---|---|---|\n"
                "| Gateway | FastAPI | Handles REST and WebSocket routing |\n"
                "| Agent Graph | LangGraph | Orchestrates state transitions |\n"
                "| LLM Model | Groq gpt-oss-120b | Executes cognitive reasoning |\n\n"
                "## 2. Multi-Agent Orchestration & Cognitive Workflow\n"
                "The pipeline operates across five dedicated cognitive agents. Each agent processes verified data and passes structured state down the graph.\n\n"
                "## 3. Context Isolation & Security Architecture\n"
                "Vector database queries filter embeddings using strict topic ID metadata to guarantee privacy and security."
            )

# Global singleton instance
llm_service = LLMService()
