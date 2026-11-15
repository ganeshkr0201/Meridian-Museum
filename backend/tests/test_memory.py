"""Tests for visitor memory persistence across sessions."""
import pytest
from app.memory.visitor_memory import VisitorMemoryService
from app.models.visitor import VisitorMemory, MemoryMode


@pytest.fixture
def memory():
    # Fresh in-memory store for each test
    from app.memory import visitor_memory as vm
    vm._GUEST_STORE.clear()
    return VisitorMemoryService(db=None)


@pytest.mark.asyncio
async def test_create_and_retrieve_memory(memory):
    mem = await memory.create_from_form(
        visitor_id="v-test-001",
        display_name="Alice",
        interests=["art", "science"],
        time_budget_minutes=60,
        accessibility_needs=[],
        language="en",
        commentary_length="medium",
        memory_mode="persistent",
    )
    assert mem.visitor_id == "v-test-001"

    retrieved = await memory.get_memory("v-test-001")
    assert retrieved is not None
    assert retrieved.display_name == "Alice"
    assert len(retrieved.interests) == 2


@pytest.mark.asyncio
async def test_memory_persists_across_calls(memory):
    await memory.create_from_form(
        visitor_id="v-persist",
        display_name="Bob",
        interests=["coins"],
        time_budget_minutes=30,
        accessibility_needs=[],
        language="en",
        commentary_length="short",
        memory_mode="persistent",
    )
    # Simulate a second call (same in-memory store)
    retrieved = await memory.get_memory("v-persist")
    assert retrieved is not None
    assert retrieved.display_name == "Bob"


@pytest.mark.asyncio
async def test_record_visit(memory):
    await memory.create_from_form(
        visitor_id="v-visit",
        display_name="Carol",
        interests=["natural_history"],
        time_budget_minutes=45,
        accessibility_needs=[],
        language="en",
        commentary_length="short",
        memory_mode="persistent",
    )
    await memory.record_visit("v-visit", "E08")
    retrieved = await memory.get_memory("v-visit")
    assert "E08" in retrieved.previously_visited_exhibits


@pytest.mark.asyncio
async def test_record_feedback(memory):
    await memory.create_from_form(
        visitor_id="v-feedback",
        display_name="Dan",
        interests=["science"],
        time_budget_minutes=50,
        accessibility_needs=[],
        language="en",
        commentary_length="medium",
        memory_mode="persistent",
    )
    await memory.record_feedback("v-feedback", "E06", liked=True, comment="Loved it")
    retrieved = await memory.get_memory("v-feedback")
    assert "E06" in retrieved.explicit_feedback
    assert retrieved.explicit_feedback["E06"]["liked"] is True


@pytest.mark.asyncio
async def test_clear_memory(memory):
    await memory.create_from_form(
        visitor_id="v-clear",
        display_name="Eve",
        interests=["art"],
        time_budget_minutes=60,
        accessibility_needs=[],
        language="en",
        commentary_length="medium",
        memory_mode="persistent",
    )
    await memory.clear_memory("v-clear")
    retrieved = await memory.get_memory("v-clear")
    assert retrieved is None


@pytest.mark.asyncio
async def test_update_preferences(memory):
    await memory.create_from_form(
        visitor_id="v-update",
        display_name="Frank",
        interests=["ancient_history"],
        time_budget_minutes=60,
        accessibility_needs=[],
        language="en",
        commentary_length="medium",
        memory_mode="persistent",
    )
    updated = await memory.update_preferences("v-update", {"display_name": "Franklin"})
    assert updated.display_name == "Franklin"
    assert updated.memory_version == 2
