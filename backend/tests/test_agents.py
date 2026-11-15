"""Tests for all five agents."""
import pytest
import asyncio
from app.agents.visitor_profile_agent import VisitorProfileAgent
from app.agents.exhibit_retrieval_agent import ExhibitRetrievalAgent
from app.agents.route_planner_agent import RoutePlannerAgent
from app.agents.commentary_writer_agent import CommentaryWriterAgent
from app.agents.guide_manager_agent import GuideManagerAgent
from app.agents.contracts import (
    VisitorProfileAgentInput, ExhibitRetrievalAgentInput,
    RoutePlannerAgentInput, CommentaryWriterAgentInput, GuideManagerAgentInput,
)
from app.memory.visitor_memory import VisitorMemoryService
from app.models.exhibit import RouteStop, RetrievedEvidence
from app.models.visit import VisitGuide


@pytest.fixture
def memory():
    return VisitorMemoryService(db=None)


@pytest.mark.asyncio
async def test_visitor_profile_agent_basic(memory):
    agent = VisitorProfileAgent(memory)
    out = await agent.run(VisitorProfileAgentInput(
        display_name="Test User",
        interests=["ancient_history", "science"],
        time_budget_minutes=60,
    ))
    assert out.visitor_profile.display_name == "Test User"
    assert len(out.visitor_profile.interests) == 2
    assert out.visitor_profile.time_budget_minutes == 60
    assert out.memory_updated is True


@pytest.mark.asyncio
async def test_visitor_profile_agent_clamps_budget(memory):
    agent = VisitorProfileAgent(memory)
    out = await agent.run(VisitorProfileAgentInput(
        display_name="Clamped",
        interests=["art"],
        time_budget_minutes=9999,
    ))
    assert out.visitor_profile.time_budget_minutes == 600


@pytest.mark.asyncio
async def test_visitor_profile_agent_invalid_interest_ignored(memory):
    agent = VisitorProfileAgent(memory)
    out = await agent.run(VisitorProfileAgentInput(
        display_name="Partial",
        interests=["ancient_history", "not_a_real_interest"],
        time_budget_minutes=45,
    ))
    assert len(out.visitor_profile.interests) == 1
    assert len(out.warnings) > 0


@pytest.mark.asyncio
async def test_exhibit_retrieval_agent_returns_candidates():
    agent = ExhibitRetrievalAgent()
    from app.memory.visitor_memory import VisitorMemoryService
    mem = VisitorMemoryService(db=None)
    profile_agent = VisitorProfileAgent(mem)
    p_out = await profile_agent.run(VisitorProfileAgentInput(
        display_name="Retrieval Tester",
        interests=["ancient_history"],
        time_budget_minutes=60,
    ))
    out = await agent.run(ExhibitRetrievalAgentInput(
        visitor_profile=p_out.visitor_profile,
        top_k=5,
    ))
    assert len(out.candidate_exhibit_ids) > 0
    assert len(out.retrieved_evidence) > 0


@pytest.mark.asyncio
async def test_route_planner_agent_respects_budget():
    from app.memory.visitor_memory import VisitorMemoryService
    mem = VisitorMemoryService(db=None)
    p_agent = VisitorProfileAgent(mem)
    r_agent = ExhibitRetrievalAgent()
    rp_agent = RoutePlannerAgent()

    p_out = await p_agent.run(VisitorProfileAgentInput(
        display_name="Budget Tester",
        interests=["natural_history"],
        time_budget_minutes=30,
    ))
    r_out = await r_agent.run(ExhibitRetrievalAgentInput(
        visitor_profile=p_out.visitor_profile, top_k=10,
    ))
    route_out = await rp_agent.run(RoutePlannerAgentInput(
        visitor_profile=p_out.visitor_profile,
        candidate_exhibit_ids=r_out.candidate_exhibit_ids,
    ))
    total = route_out.total_visit_minutes + route_out.total_walking_minutes
    assert total <= p_out.visitor_profile.time_budget_minutes + 5  # 5-min grace


@pytest.mark.asyncio
async def test_route_planner_agent_excludes_busy_gallery():
    from app.memory.visitor_memory import VisitorMemoryService
    mem = VisitorMemoryService(db=None)
    p_agent = VisitorProfileAgent(mem)
    r_agent = ExhibitRetrievalAgent()
    rp_agent = RoutePlannerAgent()

    p_out = await p_agent.run(VisitorProfileAgentInput(
        display_name="Busy Tester",
        interests=["ancient_history", "coins"],
        time_budget_minutes=90,
    ))
    r_out = await r_agent.run(ExhibitRetrievalAgentInput(
        visitor_profile=p_out.visitor_profile, top_k=12,
    ))
    route_out = await rp_agent.run(RoutePlannerAgentInput(
        visitor_profile=p_out.visitor_profile,
        candidate_exhibit_ids=r_out.candidate_exhibit_ids,
        busy_gallery_ids=["G01"],
    ))
    # No stop should be in G01
    for stop in route_out.route:
        assert stop.gallery_id != "G01"


@pytest.mark.asyncio
async def test_commentary_writer_agent_produces_all_stops():
    from app.memory.visitor_memory import VisitorMemoryService
    mem = VisitorMemoryService(db=None)
    p_agent = VisitorProfileAgent(mem)
    r_agent = ExhibitRetrievalAgent()
    rp_agent = RoutePlannerAgent()
    cw_agent = CommentaryWriterAgent()

    p_out = await p_agent.run(VisitorProfileAgentInput(
        display_name="Commentary Tester",
        interests=["art"],
        time_budget_minutes=60,
    ))
    r_out = await r_agent.run(ExhibitRetrievalAgentInput(
        visitor_profile=p_out.visitor_profile, top_k=10,
    ))
    route_out = await rp_agent.run(RoutePlannerAgentInput(
        visitor_profile=p_out.visitor_profile,
        candidate_exhibit_ids=r_out.candidate_exhibit_ids,
    ))
    cw_out = await cw_agent.run(CommentaryWriterAgentInput(
        visitor_profile=p_out.visitor_profile,
        route=route_out.route,
        retrieved_evidence=r_out.retrieved_evidence,
    ))
    for stop in route_out.route:
        assert stop.exhibit_id in cw_out.commentaries
        c = cw_out.commentaries[stop.exhibit_id]
        assert len(c.commentary) > 20
        assert len(c.source_references) > 0


@pytest.mark.asyncio
async def test_guide_manager_agent_validates_guide():
    from app.memory.visitor_memory import VisitorMemoryService
    import json, os
    mem = VisitorMemoryService(db=None)
    p_agent = VisitorProfileAgent(mem)
    r_agent = ExhibitRetrievalAgent()
    rp_agent = RoutePlannerAgent()
    cw_agent = CommentaryWriterAgent()
    gm_agent = GuideManagerAgent()

    p_out = await p_agent.run(VisitorProfileAgentInput(
        display_name="Guide Tester",
        interests=["science", "technology"],
        time_budget_minutes=60,
    ))
    r_out = await r_agent.run(ExhibitRetrievalAgentInput(
        visitor_profile=p_out.visitor_profile, top_k=10,
    ))
    route_out = await rp_agent.run(RoutePlannerAgentInput(
        visitor_profile=p_out.visitor_profile,
        candidate_exhibit_ids=r_out.candidate_exhibit_ids,
    ))
    cw_out = await cw_agent.run(CommentaryWriterAgentInput(
        visitor_profile=p_out.visitor_profile,
        route=route_out.route,
        retrieved_evidence=r_out.retrieved_evidence,
    ))
    DATA_DIR = os.path.join(os.path.dirname(__file__), "../app/data")
    with open(os.path.join(DATA_DIR, "exhibits.json")) as f:
        exhibits = json.load(f)
    tag_map = {e["exhibit_id"]: e.get("tags", []) for e in exhibits}

    guide, gm_out = await gm_agent.run(
        GuideManagerAgentInput(
            visitor_profile=p_out.visitor_profile,
            route_output=route_out,
            commentary_output=cw_out,
            retrieved_evidence=r_out.retrieved_evidence,
            visit_id="test-visit-001",
        ),
        exhibit_tag_map=tag_map,
    )
    assert isinstance(guide, VisitGuide)
    assert guide.visit_id == "test-visit-001"
