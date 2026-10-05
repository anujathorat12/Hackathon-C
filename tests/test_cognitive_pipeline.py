import os
import sys
import pytest
import asyncio
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.agents.cognitive.requirement_agent import requirement_agent, StructuredRequirements
from app.agents.cognitive.planning_agent import planning_agent, ContentPlan
from app.agents.cognitive.research_agent import research_agent, KnowledgePackage
from app.agents.cognitive.generation_agent import generation_agent
from app.agents.cognitive.review_agent import review_agent, ReviewChangelog
from app.services.vector_service import vector_service
from app.orchestration.pipeline_graph import pipeline_graph, PipelineGraphState
from app.orchestration.pipeline_runner import run_pipeline_async

def test_requirement_agent_structured_output():
    """Validates Agent 1 parses objectives, audience, and constraints into StructuredRequirements."""
    reqs = requirement_agent.run(
        title="Autonomous Clinical AI",
        description="Medical triage decision support system.",
        user_instructions="Target hospital ER staff."
    )
    assert isinstance(reqs, StructuredRequirements)
    assert reqs.objective is not None and len(reqs.objective) > 0
    assert reqs.target_audience is not None
    assert len(reqs.key_deliverables) > 0
    assert reqs.tone is not None

def test_planning_agent_all_supported_formats():
    """Validates Agent 2 builds custom outlines for PPT, DOCX, MD, and PDF formats."""
    reqs = requirement_agent.run(title="Format Test", description="Multi-format document generation.")
    
    for fmt in ["PPT", "DOCX", "MD", "PDF"]:
        plan = planning_agent.run(title="Format Test", target_format=fmt, requirements=reqs)
        assert isinstance(plan, ContentPlan)
        assert plan.target_format == fmt
        assert len(plan.sections) >= 3
        for sec in plan.sections:
            assert sec.section_id is not None
            assert sec.heading is not None
            assert sec.target_word_count > 0

def test_research_agent_and_vector_topic_isolation():
    """Validates Agent 4 retrieves facts strictly filtered by topic_id with zero context leakage."""
    topic_a = "topic_health_101"
    topic_b = "topic_finance_202"

    vector_service.seed_topic_knowledge(topic_a, [
        {"title": "Cardiology Guidelines", "content": "Ejection fraction below 40% indicates heart failure.", "source": "AHA 2026"}
    ])
    vector_service.seed_topic_knowledge(topic_b, [
        {"title": "Fiscal Regulations", "content": "Capital adequacy ratio must exceed 10.5%.", "source": "SEC 2026"}
    ])

    # Query topic_a
    results_a = vector_service.query_topic_knowledge(topic_a, "heart failure", top_k=2)
    assert all(r["topic_id"] == topic_a for r in results_a)
    assert any("Cardiology" in r["title"] for r in results_a)

    # Query topic_b to verify zero context bleed
    results_b = vector_service.query_topic_knowledge(topic_b, "ratio", top_k=2)
    assert all(r["topic_id"] == topic_b for r in results_b)
    assert not any("Cardiology" in r["title"] for r in results_b)

def test_generation_agent_style_rules():
    """Validates Agent 5 drafts structured markdown with active voice and headers."""
    reqs = requirement_agent.run(title="System Design", description="Distributed cache architecture.")
    plan = planning_agent.run(title="System Design", target_format="DOCX", requirements=reqs)
    knowledge = research_agent.run(topic_id="test_topic_gen", title="System Design", plan=plan)

    template_guidance = {
        "template_type": "DOCX",
        "typography": {"heading_font": "Calibri"},
        "layout_rules": {"max_bullets_per_slide": 5}
    }

    draft = generation_agent.run(plan=plan, knowledge=knowledge, template_guidance=template_guidance)
    assert isinstance(draft, str)
    assert len(draft) > 100
    assert "# " in draft or "## " in draft

def test_review_agent_quality_auditing():
    """Validates Agent 6 readability calculations (Grade 8-10) and changelog generation."""
    sample_text = (
        "# High Performance Architecture\n\n"
        "The distributed system processes incoming telemetry requests using an asynchronous event queue. "
        "Engineers structure microservices to guarantee isolated fault domains across multiple cloud environments. "
        "The system enforces strict data validation pipelines to prevent invalid state transitions."
    )

    refined, changelog = review_agent.run(sample_text)
    assert isinstance(refined, str)
    assert isinstance(changelog, ReviewChangelog)
    assert 7.0 <= changelog.reading_grade_level <= 11.0
    assert changelog.redundancies_removed >= 0
    assert changelog.sentences_shortened >= 0

def test_langgraph_conditional_branching():
    """Validates template guidance conditional branching in pipeline graph."""
    # Branch 1: Fallback template guidance
    guidance_default = pipeline_graph.load_template_guidance(None)
    assert "template_type" in guidance_default

    # Branch 2: Custom template path
    mock_path = os.path.join(os.path.dirname(__file__), "..", "shared", "fixtures", "sample_template_guidance.json")
    guidance_custom = pipeline_graph.load_template_guidance(mock_path)
    assert guidance_custom.get("template_type") == "DOCX"

def test_full_5_agent_pipeline_execution_sequence():
    """Validates end-to-end execution of the 5-agent pipeline producing valid progress events."""
    async def _execute():
        events = []
        async for event in run_pipeline_async(
            title="End-to-End Test Cycle",
            description="Testing full multi-agent cycle execution without discrepancies.",
            target_format="DOCX"
        ):
            events.append(event)
        return events

    # Each agent also emits a live RUNNING frame before it starts; check the completion frames.
    events = [e for e in asyncio.run(_execute()) if e.status != "RUNNING"]

    # Verify 6 stage telemetry frames emitted
    assert len(events) == 6

    # Verify sequential progress percentages
    progress_levels = [e.progress_percent for e in events]
    assert progress_levels == [15, 30, 45, 60, 75, 85]

    # Verify expected agent progression sequence
    agent_names = [e.agent_name for e in events]
    assert agent_names == [
        "Requirement Analysis Agent",
        "Planning Agent",
        "Reference Analysis Agent",
        "Research & Enrichment Agent",
        "Content Generation Agent",
        "Content Review Agent"
    ]

    # Verify final stage pauses at WAITING_FOR_REVIEW for human approval
    final_event = events[-1]
    assert final_event.status == "WAITING_FOR_REVIEW"
    assert "refined_content_preview" in final_event.payload
    assert final_event.payload["reading_grade_level"] > 0.0
