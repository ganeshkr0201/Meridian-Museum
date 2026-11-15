"""
Shared Visitor-Preference Memory Service
Provides read/write access to persistent visitor memory in MongoDB.
Every agent reads through this service; writes are explicit and justified.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any
from app.models.visitor import VisitorMemory, InterestCategory, AccessibilityNeed, Language, CommentaryLength, MemoryMode
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory fallback for guest / test mode (keyed by visitor_id)
_GUEST_STORE: dict[str, dict] = {}


class VisitorMemoryService:
    """Manages reading and writing visitor preference memory."""

    def __init__(self, db=None):
        """
        Args:
            db: Motor AsyncIOMotorDatabase instance. If None, falls back to in-memory store.
        """
        self._db = db

    async def get_memory(self, visitor_id: str) -> VisitorMemory | None:
        """Retrieve existing memory for a visitor. Returns None if not found."""
        if self._db is not None:
            doc = await self._db.visitor_memory.find_one({"visitor_id": visitor_id})
            if doc:
                doc.pop("_id", None)
                return VisitorMemory(**doc)
        else:
            raw = _GUEST_STORE.get(visitor_id)
            if raw:
                return VisitorMemory(**raw)
        return None

    async def save_memory(self, memory: VisitorMemory) -> None:
        """Persist (upsert) visitor memory."""
        memory.updated_at = datetime.utcnow()
        data = memory.model_dump()
        if self._db is not None:
            await self._db.visitor_memory.replace_one(
                {"visitor_id": memory.visitor_id}, data, upsert=True
            )
        else:
            _GUEST_STORE[memory.visitor_id] = data
        logger.debug("Saved memory for visitor %s", memory.visitor_id)

    async def update_preferences(self, visitor_id: str, updates: dict[str, Any]) -> VisitorMemory | None:
        """Apply partial updates to a visitor's memory. Only updates supplied keys."""
        mem = await self.get_memory(visitor_id)
        if mem is None:
            return None
        for key, value in updates.items():
            if hasattr(mem, key):
                setattr(mem, key, value)
        mem.memory_version += 1
        await self.save_memory(mem)
        return mem

    async def record_visit(self, visitor_id: str, exhibit_id: str) -> None:
        """Record that a visitor completed a stop at an exhibit."""
        mem = await self.get_memory(visitor_id)
        if mem is None:
            return
        if exhibit_id not in mem.previously_visited_exhibits:
            mem.previously_visited_exhibits.append(exhibit_id)
        await self.save_memory(mem)

    async def record_skip(self, visitor_id: str, exhibit_id: str, reason: str) -> None:
        """Record that an exhibit was skipped and why."""
        mem = await self.get_memory(visitor_id)
        if mem is None:
            return
        mem.previously_skipped_exhibits.append({"exhibit_id": exhibit_id, "reason": reason})
        await self.save_memory(mem)

    async def record_feedback(self, visitor_id: str, exhibit_id: str, liked: bool, comment: str = "") -> None:
        """Record explicit visitor feedback (liked/disliked) for an exhibit topic."""
        mem = await self.get_memory(visitor_id)
        if mem is None:
            return
        mem.explicit_feedback[exhibit_id] = {"liked": liked, "comment": comment}
        await self.save_memory(mem)

    async def clear_memory(self, visitor_id: str) -> None:
        """Delete all stored memory for a visitor."""
        if self._db is not None:
            await self._db.visitor_memory.delete_one({"visitor_id": visitor_id})
        else:
            _GUEST_STORE.pop(visitor_id, None)
        logger.info("Cleared memory for visitor %s", visitor_id)

    async def create_from_form(
        self,
        visitor_id: str,
        display_name: str,
        interests: list[str],
        time_budget_minutes: int,
        accessibility_needs: list[str],
        language: str,
        commentary_length: str,
        memory_mode: str,
    ) -> VisitorMemory:
        """Create or update memory from visitor form submission."""
        existing = await self.get_memory(visitor_id)

        interest_enums = [InterestCategory(i) for i in interests if i in InterestCategory._value2member_map_]
        accessibility_enums = [AccessibilityNeed(a) for a in accessibility_needs if a in AccessibilityNeed._value2member_map_]

        if existing and existing.memory_mode == MemoryMode.PERSISTENT:
            # Preserve explicit preferences; update with new form data
            existing.display_name = display_name
            existing.interests = interest_enums
            existing.preferred_language = Language(language) if language in Language._value2member_map_ else Language.ENGLISH
            existing.preferred_commentary_length = CommentaryLength(commentary_length) if commentary_length in CommentaryLength._value2member_map_ else CommentaryLength.MEDIUM
            existing.accessibility_needs = accessibility_enums
            existing.memory_version += 1
            await self.save_memory(existing)
            return existing

        new_memory = VisitorMemory(
            visitor_id=visitor_id,
            display_name=display_name,
            interests=interest_enums,
            interest_weights={i: 1.0 for i in interests},
            preferred_language=Language(language) if language in Language._value2member_map_ else Language.ENGLISH,
            preferred_commentary_length=CommentaryLength(commentary_length) if commentary_length in CommentaryLength._value2member_map_ else CommentaryLength.MEDIUM,
            accessibility_needs=accessibility_enums,
            memory_mode=MemoryMode(memory_mode) if memory_mode in MemoryMode._value2member_map_ else MemoryMode.GUEST,
        )
        await self.save_memory(new_memory)
        return new_memory
