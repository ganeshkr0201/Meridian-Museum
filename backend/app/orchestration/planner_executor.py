"""
Planner-Executor Orchestrator
Coordinates all five agents in the correct dependency order,
records workflow traces, handles retries, and supports crowd-aware replanning.

Architecture:
  User Request → Orchestrator
    → VisitorProfileAgent   (reads/writes shared memory)
    → ExhibitRetrievalAgent (RAG: catalogue + curator notes)
    → RoutePlannerAgent     (walking distance + opening hours + crowd status)
    → CommentaryWriterAgent (grounded notes + citations)
    → GuideManagerAgent     (validation + final guide)
"""

from __future__ import annotations
import json
import os
import uuid
from datetime import datetime
from app.orchestration.workflow_state import WorkflowState
from app.agents.visitor_profile_agent import VisitorProfileAgent
from app.agents.exhibit_retrieval_agent import ExhibitRetrievalAgent
from app.agents.route_planner_agent import RoutePlannerAgent
from app.agents.commentary_writer_agent import CommentaryWriterAgent
from app.agents.guide_manager_agent import GuideManagerAgent
from app.agents.contracts import (
    VisitorProfileAgentInput,
    ExhibitRetrievalAgentInput,
    RoutePlannerAgentInput,
    CommentaryWriterAgentInput,
    GuideManagerAgentInput,
)
from app.memory.visitor_memory import VisitorMemoryService
from app.models.visit import VisitGuide
from app.core.logging import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")

MAX_RETRIES = 2


def _load_exhibit_tag_map() -> dict[str, list[str]]:
    with open(EXHIBITS_FILE, encoding="utf-8") as f:
        exhibits = json.load(f)
    return {e["exhibit_id"]: e.get("tags", []) for e in exhibits}


class PlannerExecutor:
    """
    Framework-based planner-executor orchestrator.
    Uses Semantic Kernel (Microsoft's open-source agent framework) to
    coordinate five specialised agents. Falls back to sequential execution
    if SK is unavailable.
    """

    def __init__(self, memory_service: VisitorMemoryService, db=None):
        self.memory_service = memory_service
        self.db = db

        # Instantiate agents (each is a separate module with typed contracts)
        self._visitor_profile_agent = VisitorProfileAgent(memory_service)
        self._retrieval_agent = ExhibitRetrievalAgent()
        self._route_planner_agent = RoutePlannerAgent()
        self._commentary_agent = CommentaryWriterAgent()
        self._guide_manager_agent = GuideManagerAgent()

        # Try to initialise Semantic Kernel
        try:
            from app.orchestration.framework_adapter import build_kernel
            self._kernel = build_kernel()
        except Exception:
            self._kernel = None

    async def plan_visit(
        self,
        form_data: dict,
        visit_id: str | None = None,
        busy_gallery_ids: list[str] | None = None,
        completed_exhibit_ids: list[str] | None = None,
        elapsed_minutes: float = 0.0,
        crowd_replan_version: int = 0,
        replan_explanation: str = "",
    ) -> tuple[VisitGuide, WorkflowState]:
        """
        Execute the full five-agent planning workflow.

        Args:
            form_data: Visitor form submission dict.
            visit_id: Optional existing visit ID (for replanning).
            busy_gallery_ids: Galleries to avoid during replanning.
            completed_exhibit_ids: Stops already visited (not re-added).
            elapsed_minutes: Time already spent (subtracted from budget).
            crowd_replan_version: Incremented on each replan.
            replan_explanation: Human-readable explanation of why replanning occurred.

        Returns:
            (VisitGuide, WorkflowState) tuple.
        """
        vid = visit_id or str(uuid.uuid4())
        state = WorkflowState(
            visit_id=vid,
            visitor_id=form_data.get("visitor_id") or "unknown",
        )
        logger.info("[Orchestrator] Starting plan for visit %s", vid)

        exhibit_tag_map = _load_exhibit_tag_map()

        # ── STEP 1: Visitor Profile Agent ──────────────────────────────────
        entry = state.start_agent(
            "VisitorProfileAgent",
            f"name={form_data.get('display_name')}, interests={form_data.get('interests')}, budget={form_data.get('time_budget_minutes')}min",
        )
        profile_output = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                profile_input = VisitorProfileAgentInput(**form_data)
                profile_output = await self._visitor_profile_agent.run(profile_input)
                state.visitor_profile_output = profile_output
                state.visitor_id = profile_output.visitor_profile.visitor_id
                state.finish_agent(
                    entry,
                    f"Profile built for visitor_id={profile_output.visitor_profile.visitor_id}, "
                    f"interests={[i.value for i in profile_output.visitor_profile.interests]}",
                )
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning("[Orchestrator] VisitorProfileAgent attempt %d failed: %s", attempt + 1, e)
                else:
                    state.finish_agent(entry, error=str(e))
                    state.mark_failed(f"VisitorProfileAgent failed: {e}")
                    raise

        # ── STEP 2: Exhibit Retrieval Agent ────────────────────────────────
        entry = state.start_agent(
            "ExhibitRetrievalAgent",
            f"interests={[i.value for i in profile_output.visitor_profile.interests]}",
        )
        retrieval_output = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                retrieval_input = ExhibitRetrievalAgentInput(
                    visitor_profile=profile_output.visitor_profile,
                    top_k=12,
                )
                retrieval_output = await self._retrieval_agent.run(retrieval_input)
                state.retrieval_output = retrieval_output
                state.finish_agent(
                    entry,
                    f"Retrieved {len(retrieval_output.candidate_exhibit_ids)} candidate exhibits.",
                )
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning("[Orchestrator] ExhibitRetrievalAgent attempt %d failed: %s", attempt + 1, e)
                else:
                    state.finish_agent(entry, error=str(e))
                    state.mark_failed(f"ExhibitRetrievalAgent failed: {e}")
                    raise

        # ── STEP 3: Route Planner Agent ────────────────────────────────────
        entry = state.start_agent(
            "RoutePlannerAgent",
            f"candidates={retrieval_output.candidate_exhibit_ids}, busy_galleries={busy_gallery_ids or []}",
        )
        route_output = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                route_input = RoutePlannerAgentInput(
                    visitor_profile=profile_output.visitor_profile,
                    candidate_exhibit_ids=retrieval_output.candidate_exhibit_ids,
                    busy_gallery_ids=busy_gallery_ids or [],
                    completed_exhibit_ids=completed_exhibit_ids or [],
                    elapsed_minutes=elapsed_minutes,
                )
                route_output = await self._route_planner_agent.run(route_input)
                state.route_output = route_output
                state.finish_agent(
                    entry,
                    f"Route: {len(route_output.route)} stops, {route_output.total_visit_minutes + route_output.total_walking_minutes:.1f} min total.",
                )
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning("[Orchestrator] RoutePlannerAgent attempt %d failed: %s", attempt + 1, e)
                else:
                    state.finish_agent(entry, error=str(e))
                    state.mark_failed(f"RoutePlannerAgent failed: {e}")
                    raise

        # ── STEP 4: Commentary Writer Agent ───────────────────────────────
        entry = state.start_agent(
            "CommentaryWriterAgent",
            f"stops={[s.exhibit_id for s in route_output.route]}",
        )
        commentary_output = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                commentary_input = CommentaryWriterAgentInput(
                    visitor_profile=profile_output.visitor_profile,
                    route=route_output.route,
                    retrieved_evidence=retrieval_output.retrieved_evidence,
                )
                commentary_output = await self._commentary_agent.run(commentary_input)
                state.commentary_output = commentary_output
                state.finish_agent(
                    entry,
                    f"Commentary written for {len(commentary_output.commentaries)} exhibits.",
                )
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning("[Orchestrator] CommentaryWriterAgent attempt %d failed: %s", attempt + 1, e)
                else:
                    state.finish_agent(entry, error=str(e))
                    state.mark_failed(f"CommentaryWriterAgent failed: {e}")
                    raise

        # ── STEP 5: Guide Manager Agent ────────────────────────────────────
        entry = state.start_agent(
            "GuideManagerAgent",
            f"visit_id={vid}",
        )
        guide = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                guide_input = GuideManagerAgentInput(
                    visitor_profile=profile_output.visitor_profile,
                    route_output=route_output,
                    commentary_output=commentary_output,
                    retrieved_evidence=retrieval_output.retrieved_evidence,
                    visit_id=vid,
                    crowd_replan_version=crowd_replan_version,
                    replan_explanation=replan_explanation,
                )
                guide, manager_out = await self._guide_manager_agent.run(
                    guide_input, exhibit_tag_map=exhibit_tag_map
                )
                state.guide = guide
                state.finish_agent(
                    entry,
                    f"Guide valid={manager_out.valid}, total={manager_out.corrected_total_minutes:.1f} min.",
                )
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning("[Orchestrator] GuideManagerAgent attempt %d failed: %s", attempt + 1, e)
                else:
                    state.finish_agent(entry, error=str(e))
                    state.mark_failed(f"GuideManagerAgent failed: {e}")
                    raise

        # Attach trace to guide
        guide.workflow_trace = state.trace
        state.mark_completed()
        logger.info("[Orchestrator] Visit %s planning complete.", vid)
        return guide, state

    async def replan(
        self,
        existing_guide: VisitGuide,
        busy_gallery_id: str,
        elapsed_minutes: float = 0.0,
        completed_exhibit_ids: list[str] | None = None,
    ) -> tuple[VisitGuide, WorkflowState]:
        """
        Crowd-aware replanning: replan only the remaining unvisited stops.
        Preserves completed stops and visitor preferences.
        """
        completed_ids = completed_exhibit_ids or existing_guide.completed_stop_ids if hasattr(existing_guide, 'completed_stop_ids') else []

        # Mark busy gallery
        from app.tools.crowd_status import set_crowd_state
        from app.models.exhibit import CrowdState
        set_crowd_state(busy_gallery_id, CrowdState.BUSY)

        replan_version = existing_guide.crowd_replan_version + 1
        explanation = (
            f"Replanned (version {replan_version}): Gallery {busy_gallery_id} was marked busy. "
            f"Remaining route recalculated avoiding that gallery."
        )

        # Reconstruct form_data from guide's visitor profile info
        form_data = {
            "display_name": existing_guide.visitor_id,
            "interests": list(existing_guide.interest_coverage.keys()),
            "time_budget_minutes": existing_guide.time_budget_minutes,
            "accessibility_needs": [],
            "language": "en",
            "commentary_length": "medium",
            "memory_mode": "persistent",
            "visitor_id": existing_guide.visitor_id,
        }

        # Retrieve full profile from memory
        mem = await self.memory_service.get_memory(existing_guide.visitor_id)
        if mem:
            form_data["interests"] = [i.value for i in mem.interests]
            form_data["accessibility_needs"] = [a.value for a in mem.accessibility_needs]
            form_data["language"] = mem.preferred_language.value
            form_data["commentary_length"] = mem.preferred_commentary_length.value
            form_data["memory_mode"] = mem.memory_mode.value
            form_data["display_name"] = mem.display_name

        new_guide, new_state = await self.plan_visit(
            form_data=form_data,
            visit_id=existing_guide.visit_id,
            busy_gallery_ids=[busy_gallery_id],
            completed_exhibit_ids=list(completed_ids),
            elapsed_minutes=elapsed_minutes,
            crowd_replan_version=replan_version,
            replan_explanation=explanation,
        )
        return new_guide, new_state
