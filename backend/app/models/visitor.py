"""Pydantic models for visitor profiles and preferences."""

from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from enum import Enum


class AccessibilityNeed(str, Enum):
    NONE = "none"
    WHEELCHAIR = "wheelchair"
    STEP_FREE = "step_free"
    REDUCED_WALKING = "reduced_walking"
    AVOID_STAIRS = "avoid_stairs"
    SEATING_BREAKS = "seating_breaks"


class Language(str, Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    HINDI = "hi"


class CommentaryLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class MemoryMode(str, Enum):
    PERSISTENT = "persistent"
    GUEST = "guest"


class InterestCategory(str, Enum):
    ANCIENT_HISTORY = "ancient_history"
    ARCHAEOLOGY = "archaeology"
    SCIENCE = "science"
    ART = "art"
    TEXTILES = "textiles"
    COINS = "coins"
    LOCAL_CULTURE = "local_culture"
    NATURAL_HISTORY = "natural_history"
    TECHNOLOGY = "technology"
    REGIONAL_CRAFT = "regional_craft"


class VisitorMemory(BaseModel):
    """Persistent visitor memory stored in MongoDB."""

    visitor_id: str
    display_name: str
    interests: list[InterestCategory] = Field(default_factory=list)
    interest_weights: dict[str, float] = Field(default_factory=dict)
    preferred_language: Language = Language.ENGLISH
    preferred_commentary_length: CommentaryLength = CommentaryLength.MEDIUM
    accessibility_needs: list[AccessibilityNeed] = Field(default_factory=list)
    memory_mode: MemoryMode = MemoryMode.PERSISTENT
    previously_visited_exhibits: list[str] = Field(default_factory=list)
    previously_skipped_exhibits: list[dict[str, Any]] = Field(default_factory=list)
    explicit_feedback: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    memory_version: int = 1


class VisitorProfile(BaseModel):
    """Normalised visitor profile produced by the Visitor Profile Agent."""

    visitor_id: str
    display_name: str
    interests: list[InterestCategory]
    interest_weights: dict[str, float]
    time_budget_minutes: int = Field(ge=1, le=600)
    accessibility_needs: list[AccessibilityNeed] = Field(default_factory=list)
    language: Language = Language.ENGLISH
    commentary_length: CommentaryLength = CommentaryLength.MEDIUM
    memory_mode: MemoryMode = MemoryMode.PERSISTENT


class VisitorFormInput(BaseModel):
    """Raw form data submitted by the visitor."""

    display_name: str = Field(min_length=1, max_length=100)
    interests: list[InterestCategory] = Field(min_length=1)
    time_budget_minutes: int = Field(ge=5, le=600)
    accessibility_needs: list[AccessibilityNeed] = Field(default_factory=list)
    language: Language = Language.ENGLISH
    commentary_length: CommentaryLength = CommentaryLength.MEDIUM
    memory_mode: MemoryMode = MemoryMode.PERSISTENT
    visitor_id: str | None = None
