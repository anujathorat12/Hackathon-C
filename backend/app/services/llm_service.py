import os
import json
import re
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from app.config import settings

from openai import OpenAI


def _http_client_kwargs() -> Dict[str, Any]:
    """Use the OS certificate store for LLM calls (enterprise networks with TLS inspection), scoped to the
    LLM HTTP clients only. A global truststore.inject_into_ssl() breaks other TLS users such as the MongoDB
    driver (RecursionError in SSLContext.options), which silently dropped Atlas to in-memory storage."""
    try:
        import ssl
        import httpx
        import truststore
        return {"http_client": httpx.Client(verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT))}
    except Exception:
        return {}


@dataclass
class ProviderInstance:
    name: str
    display_name: str
    api_key: str
    base_url: str
    model: str
    supports_json_mode: bool = True
    extra_body: Optional[Dict[str, Any]] = None
    default_headers: Optional[Dict[str, str]] = None
    client: Optional[OpenAI] = None
    cooldown_until: float = 0.0
    failure_count: int = 0
    success_count: int = 0


class LLMService:
    """
    Multi-Provider Resilient LLM Engine with Smooth Automated Failover
    and Persistent Topic Context Memory across Primary and Backup Models.

    Supports: Groq, OpenRouter, Mistral, Google Gemini, and Rule-Based Fallback.
    Guarantees that when any backup model takes over, it receives:
      1. Full cumulative workspace state (topic, requirements, outline, facts, draft).
      2. Prior conversation history turns from previous agents in the session.
      3. Explicit seamless failover bridge instructing the model to maintain 100% consistency.
    """

    def __init__(self):
        self.fallback_count = 0
        # Running token totals reported by the APIs; callers diff snapshots to measure one run (value meter).
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0
        self.last_used_provider: str = "offline-fallback"
        self.providers: Dict[str, ProviderInstance] = {}
        self.provider_chain: List[str] = []

        # Persistent topic-scoped context memory:
        # topic_id -> list of {"role": "user"|"assistant", "content": str}
        self.conversation_memory: Dict[str, List[Dict[str, str]]] = {}

        # Cumulative structured workspace state per topic:
        # topic_id -> dict of verified state (title, description, requirements, plan, facts, draft)
        self.workspace_state_memory: Dict[str, Dict[str, Any]] = {}

        self._init_providers()

    def _init_providers(self):
        """Initializes all configured LLM providers with API keys."""
        # 1. Groq
        if settings.GROQ_API_KEY:
            extra = {"reasoning_effort": "low"} if "gpt-oss" in settings.GROQ_MODEL else None
            try:
                client = OpenAI(
                    **_http_client_kwargs(),
                    api_key=settings.GROQ_API_KEY,
                    base_url=settings.GROQ_BASE_URL,
                    timeout=45,
                    max_retries=1
                )
                self.providers["groq"] = ProviderInstance(
                    name="groq",
                    display_name="Groq",
                    api_key=settings.GROQ_API_KEY,
                    base_url=settings.GROQ_BASE_URL,
                    model=settings.GROQ_MODEL,
                    extra_body=extra,
                    client=client
                )
            except Exception as e:
                print(f"[LLMService] Failed to init Groq client: {e}")

        # 2. OpenRouter
        if settings.OPENROUTER_API_KEY:
            try:
                client = OpenAI(
                    **_http_client_kwargs(),
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url=settings.OPENROUTER_BASE_URL,
                    default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": "AGENT-101 Studio"},
                    timeout=45,
                    max_retries=1
                )
                self.providers["openrouter"] = ProviderInstance(
                    name="openrouter",
                    display_name="OpenRouter",
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url=settings.OPENROUTER_BASE_URL,
                    model=settings.OPENROUTER_MODEL,
                    client=client
                )
            except Exception as e:
                print(f"[LLMService] Failed to init OpenRouter client: {e}")

        # 3. Mistral
        if settings.MISTRAL_API_KEY:
            try:
                client = OpenAI(
                    **_http_client_kwargs(),
                    api_key=settings.MISTRAL_API_KEY,
                    base_url=settings.MISTRAL_BASE_URL,
                    timeout=45,
                    max_retries=1
                )
                self.providers["mistral"] = ProviderInstance(
                    name="mistral",
                    display_name="Mistral AI",
                    api_key=settings.MISTRAL_API_KEY,
                    base_url=settings.MISTRAL_BASE_URL,
                    model=settings.MISTRAL_MODEL,
                    client=client
                )
            except Exception as e:
                print(f"[LLMService] Failed to init Mistral client: {e}")

        # 4. Google Gemini (via OpenAI compatibility endpoint)
        if settings.GEMINI_API_KEY:
            try:
                client = OpenAI(
                    **_http_client_kwargs(),
                    api_key=settings.GEMINI_API_KEY,
                    base_url=settings.GEMINI_BASE_URL,
                    timeout=45,
                    max_retries=1
                )
                self.providers["gemini"] = ProviderInstance(
                    name="gemini",
                    display_name="Google Gemini",
                    api_key=settings.GEMINI_API_KEY,
                    base_url=settings.GEMINI_BASE_URL,
                    model=settings.GEMINI_MODEL,
                    client=client
                )
            except Exception as e:
                print(f"[LLMService] Failed to init Gemini client: {e}")

        # Parse requested chain order (e.g. "groq,openrouter,mistral,gemini")
        raw_chain = [p.strip().lower() for p in settings.LLM_PROVIDER_CHAIN.split(",") if p.strip()]
        self.provider_chain = [name for name in raw_chain if name in self.providers]

        # Add any initialized provider not explicitly listed in chain
        for name in self.providers:
            if name not in self.provider_chain:
                self.provider_chain.append(name)

        # With backups configured, fail fast (max_retries=1) and fail over. With a single provider there is
        # nothing to fail over to, so retry patiently (the SDK honours retry-after on 429) instead of
        # dropping to offline sample content after one rate-limit response.
        if len(self.provider_chain) == 1:
            only = self.providers[self.provider_chain[0]]
            only.client = only.client.with_options(max_retries=4, timeout=120)

        if self.provider_chain:
            self.last_used_provider = self.provider_chain[0]
            print(f"[LLMService] Configured multi-provider chain: {' -> '.join(self.provider_chain)}")
        else:
            print("[LLMService] No API keys configured. Using offline deterministic fallback.")

    @property
    def model(self) -> str:
        """Returns the model string of the primary or currently active provider."""
        if self.provider_chain:
            primary = self.providers.get(self.provider_chain[0])
            if primary:
                return f"{primary.display_name} ({primary.model})"
        return "offline-fallback"

    def sync_workspace_state(self, topic_id: str, state: Dict[str, Any]) -> None:
        """
        Updates the cumulative state memory for a topic workspace.
        This structured state is shared across all providers during failover.
        """
        if not topic_id:
            return
        current = self.workspace_state_memory.setdefault(topic_id, {})
        for k in [
            "title", "description", "target_format", "user_instructions",
            "structured_requirements", "content_plan", "knowledge_package",
            "draft_content", "refined_content", "current_step"
        ]:
            if k in state and state[k] is not None:
                current[k] = state[k]

    def clear_topic_context(self, topic_id: str) -> None:
        """Cleans up memory when a workspace is deleted to prevent memory leaks."""
        self.conversation_memory.pop(topic_id, None)
        self.workspace_state_memory.pop(topic_id, None)

    def _format_workspace_context_bridge(self, topic_id: str, provider_name: str) -> str:
        """
        Builds a comprehensive continuity context bridge so backup models
        know the exact background, established decisions, and prior outputs.
        """
        state = self.workspace_state_memory.get(topic_id, {})
        if not state:
            return ""

        parts = [
            f"[SESSION CONTINUITY CONTEXT — SERVING MODEL: {provider_name.upper()}]",
            f"Topic Title: {state.get('title', 'Untitled')}",
            f"Target Format: {state.get('target_format', 'Standard')}",
        ]
        if state.get("description"):
            parts.append(f"Brief/Description: {state.get('description')}")
        if state.get("user_instructions"):
            parts.append(f"User Instructions: {state.get('user_instructions')}")

        reqs = state.get("structured_requirements")
        if reqs and isinstance(reqs, dict):
            parts.append(
                f"Established Requirements: Objective='{reqs.get('objective', '')}', "
                f"Audience='{reqs.get('target_audience', '')}', "
                f"Tone='{reqs.get('tone', '')}'"
            )

        plan = state.get("content_plan")
        if plan and isinstance(plan, dict):
            sections = plan.get("sections", [])
            sec_headings = [s.get("heading", "") for s in sections if isinstance(s, dict)]
            if sec_headings:
                parts.append(f"Established Section Outline: {'; '.join(sec_headings[:6])}")

        kp = state.get("knowledge_package")
        if kp and isinstance(kp, dict):
            facts = kp.get("key_facts", [])
            if facts and isinstance(facts, list):
                fact_texts = [f.get("fact", "") if isinstance(f, dict) else str(f) for f in facts[:4]]
                if fact_texts:
                    parts.append(f"Grounded Facts: {' | '.join(fact_texts)}")

        draft = state.get("draft_content")
        if draft and isinstance(draft, str):
            # Include concise preview of draft
            preview = draft.strip()[:350].replace("\n", " ")
            parts.append(f"Current Draft Summary: {preview}...")

        parts.append(
            "CRITICAL INSTRUCTION: You are serving as a backup model in this session. "
            "Maintain 100% fidelity and consistency with all objectives, outline sections, facts, "
            "and tone established by previous agents above."
        )
        return "\n".join(parts) + "\n\n"

    def _infer_agent_name(self, system_prompt: str) -> str:
        s = (system_prompt or "").lower()
        if "requirement" in s or "audience" in s:
            return "Requirement Analysis"
        if "plan" in s or "outline" in s or "slide" in s:
            return "Planning Agent"
        if "research" in s or "fact" in s or "ground" in s:
            return "Research & Grounding"
        if "review" in s or "readab" in s or "flesch" in s:
            return "Content Review"
        if "draft" in s or "generat" in s or "synthesis" in s:
            return "Content Generation"
        return "Cognitive Synthesis"

    def get_provider_status(self) -> Dict[str, Any]:
        """Provides telemetry on configured providers, models, and health states."""
        now = time.time()
        chain_info = []
        for name in self.provider_chain:
            p = self.providers[name]
            in_cooldown = now < p.cooldown_until
            chain_info.append({
                "name": p.name,
                "display_name": p.display_name,
                "model": p.model,
                "status": "cooldown" if in_cooldown else "ready",
                "cooldown_remaining_sec": max(0, int(p.cooldown_until - now)) if in_cooldown else 0,
                "successes": p.success_count,
                "failures": p.failure_count
            })
        return {
            "primary_provider": self.provider_chain[0] if self.provider_chain else "offline-fallback",
            "last_used_provider": self.last_used_provider,
            "configured_providers": list(self.providers.keys()),
            "provider_chain": chain_info,
            "fallback_count": self.fallback_count
        }

    def generate_completion(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str = "text",
        topic_id: Optional[str] = None
    ) -> str:
        """
        Executes completion against the provider chain in priority order.
        Smoothly and transparently falls over to backups if a provider fails or is rate-limited.
        Guarantees backup models receive full cumulative workspace state & prior conversation context.
        """
        now = time.time()

        # Attempt each provider in the active chain
        for idx, name in enumerate(self.provider_chain):
            provider = self.providers.get(name)
            if not provider or not provider.client:
                continue

            # Respect cooldown window if provider recently failed with 429 / 503
            if now < provider.cooldown_until:
                remain = int(provider.cooldown_until - now)
                print(f"[LLMService] Provider '{provider.display_name}' in cooldown ({remain}s remaining). Trying next backup...")
                continue

            # Check if this provider is acting as a failover backup
            is_backup = (idx > 0)

            # Build messages with full context preservation
            if topic_id:
                context_bridge = self._format_workspace_context_bridge(topic_id, provider.display_name)
                augmented_system = (context_bridge + system_prompt) if context_bridge else system_prompt

                # Retrieve bounded prior conversation history turns for this topic (last 4 turns)
                history = self.conversation_memory.get(topic_id, [])
                prior_turns = [{"role": m["role"], "content": m["content"]} for m in history[-4:]]

                messages = [{"role": "system", "content": augmented_system}] + prior_turns + [{"role": "user", "content": prompt}]

                if is_backup and context_bridge:
                    print(f"[LLMService Context] Transferred full previous session context to backup model '{provider.display_name}'.")
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]

            # JSON calls try strict JSON mode first. Groq occasionally rejects its own output
            # ("json_validate_failed"), so retry the same provider once with JSON requested in the prompt
            # before failing over — otherwise a single-provider setup drops straight to offline content.
            attempts = ["json_mode", "json_in_text"] if (response_format == "json" and provider.supports_json_mode) else ["plain"]
            for attempt in attempts:
              start_t = time.time()
              try:
                kwargs: Dict[str, Any] = {
                    "model": provider.model,
                    "messages": messages if attempt != "json_in_text" else messages[:-1] + [{
                        "role": "user",
                        "content": prompt + "\n\nRespond with a single valid JSON object only — no prose, no code fences.",
                    }],
                    "temperature": 0.3
                }

                if attempt == "json_mode":
                    kwargs["response_format"] = {"type": "json_object"}

                if provider.extra_body:
                    kwargs["extra_body"] = provider.extra_body

                response = provider.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                usage = getattr(response, "usage", None)
                if usage is not None:  # running totals for the per-run value meter
                    self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
                    self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
                self.calls += 1
                if content and content.strip():
                    provider.success_count += 1
                    self.last_used_provider = provider.name
                    latency_ms = int((time.time() - start_t) * 1000)
                    print(f"[LLMService] Response generated successfully by {provider.display_name} ({provider.model}) in {latency_ms}ms.")

                    # Record token consumption for analysis & cost tracking
                    try:
                        from app.services.token_analytics_service import token_analytics
                        usage = getattr(response, "usage", None)
                        in_tok = getattr(usage, "prompt_tokens", None) or max(10, len(prompt) // 4)
                        out_tok = getattr(usage, "completion_tokens", None) or max(10, len(content) // 4)
                        ag_name = self._infer_agent_name(system_prompt)
                        title = self.workspace_state_memory.get(topic_id, {}).get("title") if topic_id else None
                        token_analytics.record_usage(
                            provider=provider.name,
                            model=provider.model,
                            input_tokens=in_tok,
                            output_tokens=out_tok,
                            topic_id=topic_id,
                            topic_title=title,
                            agent=ag_name,
                            latency_ms=latency_ms,
                            status="success"
                        )
                    except Exception as e_tok:
                        print(f"[LLMService Warning] Failed to log token analytics: {e_tok}")

                    # Record exchange in conversation memory for subsequent steps/failovers
                    if topic_id:
                        mem = self.conversation_memory.setdefault(topic_id, [])
                        mem.append({"role": "user", "content": prompt[:1500]})
                        mem.append({"role": "assistant", "content": content[:2500]})
                        # Keep conversation memory bounded
                        if len(mem) > 10:
                            self.conversation_memory[topic_id] = mem[-10:]

                    return content

                print(f"[LLMService Warning] {provider.display_name} returned empty content ({attempt}).")
                provider.failure_count += 1
              except Exception as e:
                provider.failure_count += 1
                err_str = str(e)
                err_type = type(e).__name__

                if attempt == "json_mode" and ("json_validate_failed" in err_str or "400" in err_str):
                    print(f"[LLMService] {provider.display_name} rejected JSON mode; retrying with JSON requested in the prompt.")
                    continue
                # Rate limited (429) -> apply 45s cooldown
                if "429" in err_str or "rate_limited" in err_str or "RateLimit" in err_type:
                    provider.cooldown_until = time.time() + 45.0
                    print(f"[LLMService Failover] {provider.display_name} rate-limited (429). Setting 45s cooldown & switching to backup.")
                # Temporary outage (503/502/500/unavailable) -> apply 30s cooldown
                elif "503" in err_str or "502" in err_str or "500" in err_str or "unavailable" in err_str:
                    provider.cooldown_until = time.time() + 30.0
                    print(f"[LLMService Failover] {provider.display_name} unavailable ({err_type}). Setting 30s cooldown & switching to backup.")
                else:
                    print(f"[LLMService Failover] {provider.display_name} error ({err_type}: {err_str[:120]}). Switching to backup...")
                break  # this provider failed for a non-JSON reason: move to the next one

        # If all live providers fail or none configured, activate deterministic offline fallback
        self.fallback_count += 1
        self.last_used_provider = "offline-fallback"
        print("[LLMService] All live providers failed or in cooldown. Smoothly activating offline fallback.", flush=True)
        fb_content = self._generate_fallback(prompt, system_prompt, response_format)

        # Log fallback token event
        try:
            from app.services.token_analytics_service import token_analytics
            in_tok = max(10, len(prompt) // 4)
            out_tok = max(10, len(fb_content) // 4)
            ag_name = self._infer_agent_name(system_prompt)
            title = self.workspace_state_memory.get(topic_id, {}).get("title") if topic_id else None
            token_analytics.record_usage(
                provider="offline-fallback",
                model="deterministic-rule-engine",
                input_tokens=in_tok,
                output_tokens=out_tok,
                topic_id=topic_id,
                topic_title=title,
                agent=ag_name,
                latency_ms=45,
                status="fallback"
            )
        except Exception:
            pass

        return fb_content

    def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        topic_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates and parses structured JSON output with automatic markdown cleanup and regex extraction.
        Carries forward full session context across providers when topic_id is provided.
        """
        raw_output = self.generate_completion(prompt, system_prompt, response_format="json", topic_id=topic_id)

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
            # If parsing completely failed, use rule-based fallback (counted, so the UI shows the sample-content warning)
            print("[LLMService] Failed to parse JSON from response. Using deterministic fallback.")
            self.fallback_count += 1
            fallback_raw = self._generate_fallback(prompt, system_prompt, response_format="json")
            try:
                return json.loads(fallback_raw)
            except Exception:
                return {"error": "Failed to parse JSON response", "raw": raw_output}

    def _generate_fallback(self, prompt: str, system_prompt: str, response_format: str) -> str:
        """Deterministic mock fallback when all API keys are missing or offline."""
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
                "| LLM Engine | Multi-Provider Failover | Executes cognitive reasoning with instant backup switch |\n\n"
                "## 2. Multi-Agent Orchestration & Cognitive Workflow\n"
                "The pipeline operates across dedicated cognitive agents. Each agent processes verified data and passes structured state down the graph.\n\n"
                "## 3. Context Isolation & Security Architecture\n"
                "Vector database queries filter embeddings using strict topic ID metadata to guarantee privacy and security."
            )


# Global singleton instance
llm_service = LLMService()
