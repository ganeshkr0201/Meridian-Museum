"""Tests for crowd-aware replanning."""
import pytest
from app.tools.crowd_status import set_crowd_state, reset_crowd_states
from app.models.exhibit import CrowdState
from app.services.visit_service import VisitService
from app.memory.visitor_memory import VisitorMemoryService


@pytest.fixture(autouse=True)
def reset_crowd():
    reset_crowd_states()
    yield
    reset_crowd_states()


@pytest.fixture
def service():
    return VisitService(db=None)


FORM = {
    "display_name": "Replan Tester",
    "interests": ["ancient_history", "science", "art"],
    "time_budget_minutes": 90,
    "accessibility_needs": [],
    "language": "en",
    "commentary_length": "short",
    "memory_mode": "guest",
}


@pytest.mark.asyncio
async def test_busy_gallery_avoided(service):
    guide = await service.plan_new_visit(FORM)
    # Pick a gallery that appears in the route
    galleries_in_route = {s.gallery_id for s in guide.route}
    if not galleries_in_route:
        pytest.skip("No route produced to test replanning.")

    busy_gid = next(iter(galleries_in_route))
    new_guide = await service.replan(guide.visit_id, busy_gid)
    assert new_guide is not None

    # Remaining (non-completed) stops should not be in busy gallery
    remaining = [s for s in new_guide.route if not s.is_completed]
    for stop in remaining:
        assert stop.gallery_id != busy_gid, (
            f"Stop {stop.exhibit_id} is in busy gallery {busy_gid}"
        )


@pytest.mark.asyncio
async def test_completed_stops_preserved(service):
    guide = await service.plan_new_visit(FORM)
    if not guide.route:
        pytest.skip("No route to test.")

    # Mark first stop completed
    first = guide.route[0]
    await service.complete_stop(guide.visit_id, first.exhibit_id)

    busy_gid = guide.route[-1].gallery_id if len(guide.route) > 1 else "G02"
    new_guide = await service.replan(guide.visit_id, busy_gid)

    completed = [s for s in new_guide.route if s.is_completed]
    completed_ids = [s.exhibit_id for s in completed]
    assert first.exhibit_id in completed_ids


@pytest.mark.asyncio
async def test_remaining_time_respected(service):
    guide = await service.plan_new_visit({**FORM, "time_budget_minutes": 40})
    if not guide.route:
        pytest.skip("No route.")

    busy_gid = "G01"
    new_guide = await service.replan(guide.visit_id, busy_gid)
    remaining = [s for s in new_guide.route if not s.is_completed]
    total = sum(s.visit_duration_minutes + s.walking_time_from_previous_minutes for s in remaining)
    assert total <= 40 + 5  # 5-min grace


@pytest.mark.asyncio
async def test_replan_has_explanation(service):
    guide = await service.plan_new_visit(FORM)
    new_guide = await service.replan(guide.visit_id, "G02")
    assert new_guide is not None
    assert new_guide.crowd_replan_version == 1
    assert len(new_guide.replan_explanation) > 0


@pytest.mark.asyncio
async def test_no_alternative_graceful(service):
    # Mark all galleries busy
    for gid in ["G01", "G02", "G03", "G04"]:
        set_crowd_state(gid, CrowdState.BUSY)
    guide = await service.plan_new_visit(FORM)
    # With all galleries busy the route should be empty but not crash
    assert guide is not None
