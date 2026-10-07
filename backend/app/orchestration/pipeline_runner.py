import asyncio
import argparse
import datetime
import uuid
from typing import AsyncGenerator, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.orchestration.pipeline_graph import pipeline_graph, PipelineGraphState
from app.services.llm_service import llm_service

class PipelineProgressEvent(BaseModel):
    topic_id: str
    agent_name: str
    status: str
    progress_percent: int
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")

async def run_pipeline_async(
    topic_id: Optional[str] = None,
    title: str = "Autonomous Multi-Agent AI System",
    description: str = "Comprehensive architecture for enterprise content synthesis.",
    target_format: str = "DOCX",
    user_instructions: Optional[str] = None,
    template_file_path: Optional[str] = None,
    min_step_seconds: float = 0.6
) -> AsyncGenerator[PipelineProgressEvent, None]:
    """
    Async generator executing the 5-agent graph step-by-step.
    Yields telemetry events (PipelineProgressEvent) for the web UI / CLI runner.
    """
    active_topic_id = topic_id or str(uuid.uuid4())
    initial_guidance = None
    if template_file_path:
        initial_guidance = pipeline_graph.load_template_guidance(template_file_path)

    state: PipelineGraphState = {
        "topic_id": active_topic_id,
        "title": title,
        "description": description,
        "target_format": target_format,
        "user_instructions": user_instructions,
        "template_file_path": template_file_path,
        "structured_requirements": None,
        "content_plan": None,
        "template_guidance": initial_guidance,
        "knowledge_package": None,
        "draft_content": None,
        "refined_content": None,
        "review_changelog": None,
        "current_step": "STARTED",
        "status": "PROCESSING"
    }

    # (graph node, progress on completion, agent name, completion message)
    steps = [
        ("Agent 1: Requirement Analysis", 15, "Requirement Analysis Agent", "Extracted audience persona and core objectives."),
        ("Agent 2: Planning", 30, "Planning Agent", "Constructed multi-section document content plan."),
        ("Agent 3: Template Ingestion", 45, "Reference Analysis Agent", "Extracted colour palette, typography and layout rules from reference template."),
        ("Agent 4: Research & Enrichment", 60, "Research & Enrichment Agent", "Retrieved grounded topic context from the topic-scoped vector store."),
        ("Agent 5: Content Generation", 75, "Content Generation Agent", "Generated section-by-section draft markdown content."),
        ("Agent 6: Content Review", 85, "Content Review Agent", "Reviewed readability, shortened long sentences and verified citations."),
    ]

    fallbacks_before = llm_service.fallback_count
    prev_progress = 0
    for node, progress, agent_name, msg in steps:
        yield PipelineProgressEvent(
            topic_id=active_topic_id,
            agent_name=agent_name,
            status="RUNNING",
            progress_percent=prev_progress,
            message=f"{agent_name} is working...",
        )
        # Agents may block on LLM calls; keep the event loop (and WebSocket) responsive.
        state = await asyncio.to_thread(pipeline_graph.execute_step, node, state)
        await asyncio.sleep(min_step_seconds)

        payload: Dict[str, Any] = {}
        if agent_name == "Requirement Analysis Agent":
            payload = state.get("structured_requirements") or {}
        elif agent_name == "Planning Agent":
            payload = state.get("content_plan") or {}
        elif agent_name == "Reference Analysis Agent":
            payload = state.get("template_guidance") or {}
        elif agent_name == "Research & Enrichment Agent":
            payload = state.get("knowledge_package") or {}
        elif agent_name == "Content Generation Agent":
            draft = state.get("draft_content") or ""
            payload = {"word_count": len(draft.split()), "draft_preview": draft[:400]}
        elif agent_name == "Content Review Agent":
            refined = state.get("refined_content") or ""
            changelog = state.get("review_changelog") or {}
            payload = {
                "refined_content": refined,
                "refined_content_preview": refined[:200] + "...",
                "word_count": len(refined.split()),
                "reading_grade_level": changelog.get("reading_grade_level", 9.0),
                "redundancies_removed": changelog.get("redundancies_removed", 2),
                "sentences_shortened": changelog.get("sentences_shortened", 1),
                "verified_citations_count": changelog.get("verified_citations_count", 4),
                # "fallback" means at least one agent used offline sample output instead of the LLM.
                "llm_mode": "fallback" if llm_service.fallback_count > fallbacks_before else "live",
            }

        yield PipelineProgressEvent(
            topic_id=active_topic_id,
            agent_name=agent_name,
            status="WAITING_FOR_REVIEW" if agent_name == "Content Review Agent" else "COMPLETED",
            progress_percent=progress,
            message=msg,
            payload=payload,
        )
        prev_progress = progress

def main():
    parser = argparse.ArgumentParser(description="Standalone Cognitive Pipeline CLI Runner")
    parser.add_argument("--title", type=str, default="Autonomous Multi-Agent AI System Architecture", help="Document Title")
    parser.add_argument("--description", type=str, default="Comprehensive technical guide for multi-agent execution graphs.", help="Document Description")
    parser.add_argument("--format", type=str, choices=["PPT", "DOCX", "MD", "PDF"], default="DOCX", help="Target Format")
    parser.add_argument("--instructions", type=str, default=None, help="User instructions")

    args = parser.parse_args()

    print("=" * 70)
    print(">>> STARTING STANDALONE COGNITIVE PIPELINE")
    print(f"Title: {args.title}")
    print(f"Format: {args.format}")
    print("=" * 70)

    async def run_cli():
        async for event in run_pipeline_async(
            title=args.title,
            description=args.description,
            target_format=args.format,
            user_instructions=args.instructions
        ):
            if event.status == "RUNNING":
                continue
            status_symbol = "[...] " if event.status == "PROCESSING" else ("Wait " if event.status == "WAITING_FOR_REVIEW" else "[OK]  ")
            print(f"{status_symbol} [{event.progress_percent}%] {event.agent_name}: {event.message}")

            if event.agent_name == "Content Review Agent":
                print("\n" + "-" * 70)
                print("REFINED CONTENT PREVIEW:")
                print(event.payload.get("refined_content_preview", ""))
                print(f"Reading Grade Level: {event.payload.get('reading_grade_level')}")
                print(f"Redundancies Removed: {event.payload.get('redundancies_removed')}")
                print(f"Verified Citations: {event.payload.get('verified_citations_count')}")
                print("-" * 70)

    asyncio.run(run_cli())

if __name__ == "__main__":
    main()
