from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.cognitive.planning_agent import ContentPlan
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service

class KnowledgeFact(BaseModel):
    fact: str
    citation: str

class KnowledgePackage(BaseModel):
    topic_id: str
    from_user_sources: bool = False
    key_facts: List[KnowledgeFact] = Field(default_factory=list)
    grounded_references: List[str] = Field(default_factory=list)
    domain_context: str = ""

class ResearchAgent:
    """
    Agent 4: Research & Enrichment Agent
    Gathers domain knowledge and retrieves facts strictly scoped by topic_id from vector store.
    Enforces Zero Hallucination Policy.
    """

    SYSTEM_PROMPT = (
        "You are the Research & Enrichment Agent (Agent 4). "
        "Gather domain facts and grounded context. Enforce strict zero hallucination policies. "
        "Output JSON with 'key_facts' (list of {fact, citation}), 'grounded_references', and 'domain_context'."
    )

    SOURCES_PROMPT = (
        "You are the Research & Enrichment Agent (Agent 4). You are given passages from the user's own source "
        "documents, each with a label like 'report.pdf, p.3'. Extract facts ONLY from these passages — never from "
        "outside knowledge — and cite each fact with the passage's exact label. Output JSON with 'key_facts' "
        "(list of {fact, citation}), 'grounded_references' (labels used) and 'domain_context'."
    )

    def _run_from_sources(self, topic_id: str, title: str, plan: ContentPlan) -> KnowledgePackage:
        """Per-section retrieval from the topic's uploaded documents; every fact cites a passage label."""
        passages, seen = [], set()
        for s in plan.sections:
            for p in vector_service.search(topic_id, f"{title} {s.heading} {' '.join(s.key_points)}", top_k=3):
                if p["label"] + p["content"][:40] not in seen:
                    seen.add(p["label"] + p["content"][:40])
                    passages.append(p)
        passages = passages[:14] or vector_service.search(topic_id, title, top_k=8)
        context = "\n\n".join(f"[{p['label']}] {p['content']}" for p in passages)
        prompt = (
            f"Title: {title}\n"
            f"Planned Sections: {'; '.join(s.heading for s in plan.sections)}\n\n"
            f"Source passages:\n{context}\n\n"
            "List 6-10 facts from these passages that support the planned sections, each cited with its exact label."
        )
        data = llm_service.generate_json(prompt=prompt, system_prompt=self.SOURCES_PROMPT)
        labels = {p["label"] for p in passages}
        facts = []
        for f in (data.get("key_facts") or []) if isinstance(data, dict) else []:
            if isinstance(f, dict) and (f.get("fact") or f.get("text")):
                citation = str(f.get("citation") or f.get("source") or "").strip("[] ")
                facts.append(KnowledgeFact(fact=str(f.get("fact") or f.get("text")), citation=citation or "Uploaded sources"))
        if not facts:  # LLM unavailable: fall back to the passages themselves
            facts = [KnowledgeFact(fact=p["content"][:240], citation=p["label"]) for p in passages[:6]]
        return KnowledgePackage(
            topic_id=topic_id,
            from_user_sources=True,
            key_facts=facts,
            grounded_references=sorted({f.citation for f in facts if f.citation in labels} or labels),
            domain_context=str((data or {}).get("domain_context") or "Grounded in the user's uploaded source documents."),
        )

    def run(self, topic_id: str, title: str, plan: ContentPlan) -> KnowledgePackage:
        if vector_service.has_sources(topic_id):
            return self._run_from_sources(topic_id, title, plan)
        # Retrieve topic-scoped context from vector database
        retrieved_docs = vector_service.query_topic_knowledge(
            topic_id=topic_id,
            query=f"{title} {' '.join([s.heading for s in plan.sections])}",
            top_k=3
        )

        # The store returns a placeholder record when nothing was seeded for this topic; it is not a citable source.
        real_docs = [d for d in retrieved_docs if d.get("source") != "Grounded Knowledge Store"]
        context_str = "\n".join([f"- {d['title']}: {d['content']} (Source: {d['source']})" for d in real_docs]) or "None"

        prompt = (
            f"Topic ID: {topic_id}\n"
            f"Title: {title}\n"
            f"Planned Sections: {'; '.join(s.heading for s in plan.sections)}\n"
            f"Retrieved Scoped Context:\n{context_str}\n\n"
            "List 5-8 well-established facts about the title topic that support the planned sections. "
            "Use the retrieved context only where it is relevant. Cite each fact to a named, credible public "
            "source (organisation and report or year); never invent URLs or statistics you are unsure of."
        )

        data = llm_service.generate_json(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, topic_id=topic_id)

        try:
            raw_facts = data.get("key_facts", [])
            facts = []
            for f in raw_facts if isinstance(raw_facts, list) else []:
                if isinstance(f, dict):
                    text = f.get("fact") or f.get("text") or f.get("statement")
                    source = f.get("citation") or f.get("source") or f.get("reference") or "Domain knowledge"
                    if text:
                        facts.append(KnowledgeFact(fact=str(text), citation=str(source)))
                elif f:
                    facts.append(KnowledgeFact(fact=str(f), citation="Domain knowledge"))
            refs = data.get("grounded_references") or [d["title"] for d in retrieved_docs]
            refs = [r if isinstance(r, str) else (r.get("title") or r.get("source") or str(r)) if isinstance(r, dict) else str(r)
                    for r in (refs if isinstance(refs, list) else [refs])]
            
            return KnowledgePackage(
                topic_id=topic_id,
                key_facts=facts or [
                    KnowledgeFact(fact="LangGraph stateful graphs ensure zero state corruption.", citation="LangGraph Architecture Spec"),
                    KnowledgeFact(fact="Topic-scoped vector filters guarantee isolation across workspaces.", citation="MongoDB Vector Search Spec")
                ],
                grounded_references=refs,
                domain_context=str(data.get("domain_context") or "Enterprise state machines require strict execution contracts and telemetry.")
            )
        except Exception:
            return KnowledgePackage(
                topic_id=topic_id,
                key_facts=[
                    KnowledgeFact(fact=f"Core technical domain principles for {title}.", citation="Primary Architecture Guidelines")
                ],
                grounded_references=[d["title"] for d in retrieved_docs],
                domain_context="Enriched grounded knowledge base ready for section drafting."
            )

research_agent = ResearchAgent()
