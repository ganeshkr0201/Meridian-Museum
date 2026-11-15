"""Tests for the planner-executor orchestration."""
import pytest
from app.orchestration.planner_executor import PlannerExecutor
from app.memory.visitor_memory import VisitorMemoryService
from app.models.visit import VisitGuide, AgentStatus


@pytest.fixture
def orchestrator():
    mem = VisitorMemoryService(db=None)
    return PlannerExecutor(mem)


FORM = {
    "display_name": "Orch Tester",
    "interests": ["science"],
    "time_budget_minutes": 50,
    "accessibility_needs": [],
    "language": "en",
    "commentary_length": "short",
    "memory_mode": "guest",
}


@pytest.mark.asyncio
async def test_orchestrator_produces_guide(orchestrator):
    guide, state = await orchestrator.plan_visit(FORM)
    assert isinstance(guide, VisitGuide)
    assert state.status == "completed"


@pytest.mark.asyncio
async def test_workflow_trace_has_five_entries(orchestrator):
    guide, state = await orchestrator.plan_visit(FORM)
    agent_names = [t.agent_name for t in state.trace]
    assert "VisitorProfileAgent" in agent_names
    assert "ExhibitRetrievalAgent" in agent_names
    assert "RoutePlannerAgent" in agent_names
    assert "CommentaryWriterAgent" in agent_names
    assert "GuideManagerAgent" in agent_names


@pytest.mark.asyncio
async def test_all_trace_entries_completed(orchestrator):
    guide, state = await orchestrator.plan_visit(FORM)
    for entry in state.trace:
        assert entry.status == AgentStatus.COMPLETED, (
            f"{entry.agent_name} status = {entry.status}: {entry.error_message}"
        )


@pytest.mark.asyncio
async def test_guide_has_visit_id(orchestrator):
    guide, state = await orchestrator.plan_visit(FORM, visit_id="fixed-id-001")
    assert guide.visit_id == "fixed-id-001"


@pytest.mark.asyncio
async def test_guide_route_is_ordered(orchestrator):
    guide, _ = await orchestrator.plan_visit(FORM)
    for i, stop in enumerate(guide.route):
        assert stop.sequence == i + 1


@pytest.mark.asyncio
async def test_guide_commentaries_match_route(orchestrator):
    guide, _ = await orchestrator.plan_visit(FORM)
    for stop in guide.route:
        assert stop.exhibit_id in guide.commentaries
