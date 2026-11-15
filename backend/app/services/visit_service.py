"""
Visit Service — coordinates visit persistence and crowd-aware replanning.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from app.orchestration.planner_executor import PlannerExecutor
from app.models.visit import VisitGuide, VisitSession
from app.memory.visitor_memory import VisitorMemoryService
from app.tools.crowd_status import set_crowd_state, get_all_crowd_states
from app.models.exhibit import CrowdState
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory session store (mirrored to DB when available)
_SESSION_STORE: dict[str, VisitSession] = {}


class VisitService:
    def __init__(self, db=None):
        self.db = db
        self.memory_service = VisitorMemoryService(db)
        self.orchestrator = PlannerExecutor(self.memory_service, db)

    async def plan_new_visit(self, form_data: dict) -> VisitGuide:
        visit_id = str(uuid.uuid4())
        guide, state = await self.orchestrator.plan_visit(form_data, visit_id=visit_id)

        session = VisitSession(
            visit_id=visit_id,
            visitor_id=guide.visitor_id,
            guide=guide,
            status="active",
        )
        await self._save_session(session)
        return guide

    async def get_visit(self, visit_id: str) -> VisitGuide | None:
        session = await self._load_session(visit_id)
        return session.guide if session else None

    async def complete_stop(self, visit_id: str, exhibit_id: str) -> VisitGuide | None:
        session = await self._load_session(visit_id)
        if not session or not session.guide:
            return None
        if exhibit_id not in session.completed_stop_ids:
            session.completed_stop_ids.append(exhibit_id)
        # Mark stop as completed in route
        for stop in session.guide.route:
            if stop.exhibit_id == exhibit_id:
                stop.is_completed = True
        session.updated_at = datetime.utcnow()
        await self._save_session(session)
        await self.memory_service.record_visit(session.visitor_id, exhibit_id)
        return session.guide

    async def replan(self, visit_id: str, busy_gallery_id: str) -> VisitGuide | None:
        session = await self._load_session(visit_id)
        if not session or not session.guide:
            return None

        completed_ids = session.completed_stop_ids
        # Calculate elapsed time from completed stops
        elapsed = sum(
            s.visit_duration_minutes + s.walking_time_from_previous_minutes
            for s in session.guide.route
            if s.exhibit_id in completed_ids
        )

        new_guide, _ = await self.orchestrator.replan(
            existing_guide=session.guide,
            busy_gallery_id=busy_gallery_id,
            elapsed_minutes=elapsed,
            completed_exhibit_ids=completed_ids,
        )

        # Preserve completed stops from original route
        completed_stops = [s for s in session.guide.route if s.is_completed]
        new_guide.route = completed_stops + new_guide.route
        # Re-sequence
        for i, stop in enumerate(new_guide.route):
            stop.sequence = i + 1

        session.guide = new_guide
        session.updated_at = datetime.utcnow()
        await self._save_session(session)
        return new_guide

    async def submit_feedback(self, visit_id: str, exhibit_id: str, liked: bool, comment: str = "") -> None:
        session = await self._load_session(visit_id)
        if not session:
            return
        await self.memory_service.record_feedback(session.visitor_id, exhibit_id, liked, comment)

    # ── Persistence helpers ────────────────────────────────────────────────

    async def _save_session(self, session: VisitSession) -> None:
        _SESSION_STORE[session.visit_id] = session
        if self.db is not None:
            data = session.model_dump(mode="json")
            await self.db.visit_sessions.replace_one(
                {"visit_id": session.visit_id}, data, upsert=True
            )

    async def _load_session(self, visit_id: str) -> VisitSession | None:
        if visit_id in _SESSION_STORE:
            return _SESSION_STORE[visit_id]
        if self.db is not None:
            doc = await self.db.visit_sessions.find_one({"visit_id": visit_id})
            if doc:
                doc.pop("_id", None)
                session = VisitSession(**doc)
                _SESSION_STORE[visit_id] = session
                return session
        return None
