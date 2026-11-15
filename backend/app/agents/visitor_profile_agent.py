"""
Agent A — Visitor Profile Agent
Validates and normalises visitor input, reads/writes shared memory,
and produces a structured VisitorProfile for downstream agents.
"""

from __future__ import annotations
import uuid
from app.agents.contracts import VisitorProfileAgentInput, VisitorProfileAgentOutput
from app.models.visitor import (
    VisitorProfile, InterestCategory, AccessibilityNeed,
    Language, CommentaryLength, MemoryMode,
)
from app.memory.visitor_memory import VisitorMemoryService
from app.core.logging import get_logger

logger = get_logger(__name__)

INTEREST_ALIASES: dict[str, str] = {
    "history": "ancient_history",
    "archaeology": "archaeology",
    "science": "science",
    "art": "art",
    "textiles": "textiles",
    "coins": "coins",
    "culture": "local_culture",
    "natural history": "natural_history",
    "technology": "technology",
    "craft": "regional_craft",
}

VALID_INTERESTS = set(InterestCategory._value2member_map_.keys())


class VisitorProfileAgent:
    """
    Validates visitor form input, resolves conflicts, reads existing memory
    for returning visitors, writes updated preferences to shared memory,
    and produces a normalised VisitorProfile.
    """

    name = "VisitorProfileAgent"

    def __init__(self, memory_service: VisitorMemoryService):
        self.memory = memory_service

    async def run(self, input_data: VisitorProfileAgentInput) -> VisitorProfileAgentOutput:
        logger.info("[%s] Running for visitor: %s", self.name, input_data.display_name)
        warnings: list[str] = []

        # 1. Resolve visitor ID
        visitor_id = input_data.visitor_id or str(uuid.uuid4())

        # 2. Normalise interests
        raw_interests = [i.lower().strip() for i in input_data.interests]
        interests: list[InterestCategory] = []
        for raw in raw_interests:
            resolved = INTEREST_ALIASES.get(raw, raw)
            if resolved in VALID_INTERESTS:
                interests.append(InterestCategory(resolved))
            else:
                warnings.append(f"Unrecognised interest '{raw}' was ignored.")

        if not interests:
            interests = [InterestCategory.ANCIENT_HISTORY]
            warnings.append("No valid interests provided. Defaulting to ancient_history.")

        # 3. Normalise accessibility
        accessibility_needs: list[AccessibilityNeed] = []
        for a in input_data.accessibility_needs:
            if a in AccessibilityNeed._value2member_map_:
                accessibility_needs.append(AccessibilityNeed(a))
            else:
                warnings.append(f"Unrecognised accessibility need '{a}' was ignored.")

        # 4. Normalise language and commentary length
        language = Language(input_data.language) if input_data.language in Language._value2member_map_ else Language.ENGLISH
        commentary_length = (
            CommentaryLength(input_data.commentary_length)
            if input_data.commentary_length in CommentaryLength._value2member_map_
            else CommentaryLength.MEDIUM
        )
        memory_mode = (
            MemoryMode(input_data.memory_mode)
            if input_data.memory_mode in MemoryMode._value2member_map_
            else MemoryMode.GUEST
        )

        # 5. Validate time budget
        time_budget = max(5, min(600, input_data.time_budget_minutes))
        if time_budget != input_data.time_budget_minutes:
            warnings.append(f"Time budget clamped to {time_budget} minutes.")

        # 6. Read existing memory and merge if applicable
        existing_memory = await self.memory.get_memory(visitor_id)
        memory_updated = False

        if existing_memory and memory_mode == MemoryMode.PERSISTENT:
            # Merge: keep user-provided data, supplement with historical
            if not interests and existing_memory.interests:
                interests = existing_memory.interests
                warnings.append("Used interests from previous visit memory.")

        # 7. Build interest weights (uniform by default; memory can boost)
        interest_weights: dict[str, float] = {i.value: 1.0 for i in interests}
        if existing_memory:
            for key, weight in existing_memory.interest_weights.items():
                if key in interest_weights:
                    interest_weights[key] = max(weight, 1.0)

        # 8. Write to memory
        await self.memory.create_from_form(
            visitor_id=visitor_id,
            display_name=input_data.display_name,
            interests=[i.value for i in interests],
            time_budget_minutes=time_budget,
            accessibility_needs=[a.value for a in accessibility_needs],
            language=language.value,
            commentary_length=commentary_length.value,
            memory_mode=memory_mode.value,
        )
        memory_updated = True

        profile = VisitorProfile(
            visitor_id=visitor_id,
            display_name=input_data.display_name,
            interests=interests,
            interest_weights=interest_weights,
            time_budget_minutes=time_budget,
            accessibility_needs=accessibility_needs,
            language=language,
            commentary_length=commentary_length,
            memory_mode=memory_mode,
        )

        logger.info("[%s] Profile built for %s (id=%s, interests=%s, budget=%dm)",
                    self.name, profile.display_name, visitor_id,
                    [i.value for i in interests], time_budget)
        return VisitorProfileAgentOutput(
            visitor_profile=profile,
            memory_updated=memory_updated,
            warnings=warnings,
        )
