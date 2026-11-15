"""Pydantic models for exhibits, galleries, and retrieved evidence."""

from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum


class AccessibilityFeature(str, Enum):
    WHEELCHAIR_ACCESSIBLE = "wheelchair_accessible"
    STEP_FREE = "step_free"
    ACCESSIBLE_SEATING = "accessible_seating"
    TACTILE_DISPLAY = "tactile_display"
    AUDIO_GUIDE = "audio_guide"
    STAIRS_REQUIRED = "stairs_required"


class CrowdState(str, Enum):
    NORMAL = "normal"
    MODERATE = "moderate"
    BUSY = "busy"
    CLOSED = "closed"


class GalleryNode(BaseModel):
    """A gallery node in the museum graph."""

    gallery_id: str
    name: str
    floor: int = 0
    x: float = 0.0
    y: float = 0.0
    is_accessible: bool = True
    crowd_state: CrowdState = CrowdState.NORMAL
    opening_hours: dict[str, str] = Field(default_factory=dict)


class GalleryEdge(BaseModel):
    """A walking path between two galleries."""

    from_gallery_id: str
    to_gallery_id: str
    distance_m: float
    walk_minutes: float
    accessible: bool = True
    has_stairs: bool = False


class Exhibit(BaseModel):
    """Full exhibit record."""

    exhibit_id: str
    title: str
    gallery_id: str
    description: str
    tags: list[str] = Field(default_factory=list)
    estimated_visit_minutes: int = Field(ge=1)
    accessibility_features: list[AccessibilityFeature] = Field(default_factory=list)
    catalogue_source_id: str = ""
    image_path: str = ""
    is_open: bool = True
    curator_note_ids: list[str] = Field(default_factory=list)


class RetrievedEvidence(BaseModel):
    """A single retrieved chunk from ChromaDB with provenance."""

    exhibit_id: str
    source_id: str
    source_title: str
    chunk_text: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)


class RouteStop(BaseModel):
    """One stop on the generated visitor route."""

    sequence: int
    exhibit_id: str
    exhibit_title: str
    gallery_id: str
    gallery_name: str
    visit_duration_minutes: int
    walking_distance_from_previous_m: float
    walking_time_from_previous_minutes: float
    planned_arrival_offset_minutes: float
    accessibility_status: str
    opening_status: str
    is_completed: bool = False


class SkippedItem(BaseModel):
    """An exhibit that was considered but excluded from the route."""

    exhibit_id: str
    title: str
    reason_code: str
    human_readable_reason: str


class ExhibitCommentary(BaseModel):
    """Grounded commentary for a single exhibit."""

    exhibit_id: str
    commentary: str
    interest_match_reason: str
    source_references: list[str]
    confidence: str
    did_you_know: str = ""
