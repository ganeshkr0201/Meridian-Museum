"""
Typed input/output contracts shared between all agents.
Every inter-agent data transfer uses these Pydantic models.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from app.models.visitor import VisitorProfile
from app.models.exhibit import RetrievedEvidence, RouteStop, SkippedItem, ExhibitCommentary


class VisitorProfileAgentInput(BaseModel):
    display_name: str
    interests: list[str]
    time_budget_minutes: int
    accessibility_needs: list[str] = Field(default_factory=list)
    language: str = "en"
    commentary_length: str = "medium"
    memory_mode: str = "persistent"
    visitor_id: str | None = None


class VisitorProfileAgentOutput(BaseModel):
    visitor_profile: VisitorProfile
    memory_updated: bool = False
    warnings: list[str] = Field(default_factory=list)


class ExhibitRetrievalAgentInput(BaseModel):
    visitor_profile: VisitorProfile
    top_k: int = 10


class ExhibitRetrievalAgentOutput(BaseModel):
    retrieved_evidence: list[RetrievedEvidence]
    candidate_exhibit_ids: list[str]
    low_confidence: bool = False
    warnings: list[str] = Field(default_factory=list)


class RoutePlannerAgentInput(BaseModel):
    visitor_profile: VisitorProfile
    candidate_exhibit_ids: list[str]
    start_time: str = "10:00"
    busy_gallery_ids: list[str] = Field(default_factory=list)
    completed_exhibit_ids: list[str] = Field(default_factory=list)
    elapsed_minutes: float = 0.0


class RoutePlannerAgentOutput(BaseModel):
    route: list[RouteStop]
    skipped_items: list[SkippedItem]
    total_visit_minutes: float
    total_walking_minutes: float
    total_walking_distance_m: float
    time_budget_fit: bool
    warnings: list[str] = Field(default_factory=list)


class CommentaryWriterAgentInput(BaseModel):
    visitor_profile: VisitorProfile
    route: list[RouteStop]
    retrieved_evidence: list[RetrievedEvidence]


class CommentaryWriterAgentOutput(BaseModel):
    commentaries: dict[str, ExhibitCommentary]
    warnings: list[str] = Field(default_factory=list)


class GuideManagerAgentInput(BaseModel):
    visitor_profile: VisitorProfile
    route_output: RoutePlannerAgentOutput
    commentary_output: CommentaryWriterAgentOutput
    retrieved_evidence: list[RetrievedEvidence]
    visit_id: str
    crowd_replan_version: int = 0
    replan_explanation: str = ""


class GuideManagerAgentOutput(BaseModel):
    valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    corrected_total_minutes: float = 0.0
