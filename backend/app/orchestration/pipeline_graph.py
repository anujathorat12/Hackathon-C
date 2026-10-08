import os
import json
from typing import Dict, Any, Optional, TypedDict, List
from pydantic import BaseModel, Field

from app.agents.cognitive.requirement_agent import requirement_agent, StructuredRequirements
from app.agents.cognitive.planning_agent import planning_agent, ContentPlan
from app.agents.cognitive.research_agent import research_agent, KnowledgePackage
from app.agents.cognitive.generation_agent import generation_agent
from app.agents.cognitive.review_agent import review_agent, ReviewChangelog
from app.services.llm_service import llm_service

class PipelineGraphState(TypedDict):
    topic_id: str
    title: str
    description: str
    target_format: str
    user_instructions: Optional[str]
    language: Optional[str]
    template_file_path: Optional[str]
    structured_requirements: Optional[Dict[str, Any]]
    content_plan: Optional[Dict[str, Any]]
    template_guidance: Optional[Dict[str, Any]]
    knowledge_package: Optional[Dict[str, Any]]
    draft_content: Optional[str]
    refined_content: Optional[str]
    review_changelog: Optional[Dict[str, Any]]
    current_step: str
    status: str

class PipelineGraph:
    """
    Stateful execution graph for the cognitive pipeline.
    Orchestrates:
    - Agent 1: Requirement Analysis
    - Agent 2: Planning
    - Agent 3 Hook / Fallback Template Guidance
    - Agent 4: Research & Enrichment
    - Agent 5: Content Generation
    - Agent 6: Content Review Audit
    """

    def __init__(self):
        self.mock_template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "shared", "fixtures", "sample_template_guidance.json"
        )

    def load_template_guidance(self, template_file_path: Optional[str]) -> Dict[str, Any]:
        """Agent 3 hook: pre-computed guidance JSON, else the ReferenceAnalysisAgent, else the frozen fixture."""
        if template_file_path and template_file_path.endswith(".json") and os.path.exists(template_file_path):
            try:
                with open(template_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        try:
            from app.agents.document.reference_agent import ReferenceAnalysisAgent
            return ReferenceAnalysisAgent().analyze_template(template_file_path).model_dump()
        except Exception as e:
            print(f"[PipelineGraph] Reference analysis failed ({e}). Using fixture.")

        # Load frozen contract fixture from shared/fixtures/sample_template_guidance.json
        if os.path.exists(self.mock_template_path):
            with open(self.mock_template_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return {
            "template_type": "DOCX",
            "color_palette": {"primary_hex": "#1B365D", "secondary_hex": "#4B6B94"},
            "typography": {"heading_font": "Calibri", "body_font": "Calibri"},
            "layout_rules": {"max_bullets_per_slide": 5}
        }

    @staticmethod
    def _source_digest(topic_id: str, max_chars: int = 6000) -> Optional[str]:
        """Labelled text of the topic's uploaded sources, so planning stays within what they cover."""
        from app.services.vector_service import vector_service
        if not vector_service.has_sources(topic_id):
            return None
        digest = "\n".join(f"[{r['label']}] {r['content']}" for r in vector_service._in_memory_store[topic_id])
        return digest[:max_chars]

    def execute_step(self, step_name: str, state: PipelineGraphState) -> PipelineGraphState:
        """Executes a single node in the graph and updates state with cross-agent context synchronization."""
        new_state = dict(state)
        topic_id = state.get("topic_id", "")
        if topic_id:
            llm_service.sync_workspace_state(topic_id, new_state)

        if step_name == "Agent 1: Requirement Analysis":
            reqs = requirement_agent.run(
                title=state["title"],
                description=state["description"],
                user_instructions=state.get("user_instructions"),
                topic_id=topic_id
            )
            new_state["structured_requirements"] = reqs.model_dump()
            new_state["current_step"] = "Requirement Analysis Complete"

        elif step_name == "Agent 2: Planning":
            if not new_state.get("template_guidance") and state.get("template_file_path"):
                new_state["template_guidance"] = self.load_template_guidance(state.get("template_file_path"))
            reqs = StructuredRequirements(**(state.get("structured_requirements") or {}))
            plan = planning_agent.run(
                title=state["title"],
                target_format=state["target_format"],
                requirements=reqs,
                language=state.get("language") or "English",
                source_digest=self._source_digest(state["topic_id"]),
                template_guidance=new_state.get("template_guidance"),
                topic_id=topic_id
            )
            new_state["content_plan"] = plan.model_dump()
            new_state["current_step"] = "Planning Complete"

        elif step_name == "Agent 3: Template Ingestion":
            guidance = self.load_template_guidance(state.get("template_file_path"))
            new_state["template_guidance"] = guidance
            new_state["current_step"] = "Template Guidance Loaded"

        elif step_name == "Agent 4: Research & Enrichment":
            plan = ContentPlan(**(state.get("content_plan") or {}))
            knowledge = research_agent.run(
                topic_id=state["topic_id"],
                title=state["title"],
                plan=plan
            )
            new_state["knowledge_package"] = knowledge.model_dump()
            new_state["current_step"] = "Research Complete"

        elif step_name == "Agent 5: Content Generation":
            plan = ContentPlan(**(state.get("content_plan") or {}))
            knowledge = KnowledgePackage(**(state.get("knowledge_package") or {}))
            guidance = state.get("template_guidance")

            draft = generation_agent.run(
                plan=plan,
                knowledge=knowledge,
                template_guidance=guidance,
                requirements=state.get("structured_requirements"),
                user_instructions=state.get("user_instructions"),
                language=state.get("language") or "English",
                topic_id=topic_id
            )
            new_state["draft_content"] = draft
            new_state["current_step"] = "Content Generation Complete"

        elif step_name == "Agent 6: Content Review":
            draft = state.get("draft_content") or f"# {state['title']}\n\nDraft content standard preview."
            refined_content, changelog = review_agent.run(draft, state.get("language") or "English", topic_id=topic_id)

            new_state["refined_content"] = refined_content
            new_state["review_changelog"] = changelog.model_dump()
            new_state["current_step"] = "Content Review Complete"
            new_state["status"] = "WAITING_FOR_REVIEW"

        if topic_id:
            llm_service.sync_workspace_state(topic_id, new_state)

        return new_state

pipeline_graph = PipelineGraph()
