"""Pydantic models for visit sessions, guides, and workflow traces."""

from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from enum import Enum
from app.models.exhibit import RouteStop, SkippedItem, ExhibitCommentary, RetrievedEvidence


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowTraceEntry(BaseModel):
    """Execution record for one agent in the workflow."""

    agent_name: str
    status: AgentStatus = AgentStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    input_summary: str = ""
    output_summary: str = ""
    error_message: str | None = None


class VisitGuide(BaseModel):
    """The final compiled personalised museum visit guide."""

    visit_id: str
    visitor_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    route: list[RouteStop] = Field(default_factory=list)
    commentaries: dict[str, ExhibitCommentary] = Field(default_factory=dict)
    skipped_items: list[SkippedItem] = Field(default_factory=list)
    total_visit_minutes: float = 0.0
    total_walking_minutes: float = 0.0
    total_walking_distance_m: float = 0.0
    time_budget_minutes: int = 0
    time_budget_fit: bool = True
    interest_coverage: dict[str, bool] = Field(default_factory=dict)
    sources: list[RetrievedEvidence] = Field(default_factory=list)
    workflow_trace: list[WorkflowTraceEntry] = Field(default_factory=list)
    crowd_replan_version: int = 0
    replan_explanation: str = ""


class VisitSession(BaseModel):
    """Persisted visit session document in MongoDB."""

    visit_id: str
    visitor_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    guide: VisitGuide | None = None
    completed_stop_ids: list[str] = Field(default_factory=list)
    status: str = "planning"


class CompletedStop(BaseModel):
    """Request body for marking a stop as completed."""

    exhibit_id: str


class FeedbackRequest(BaseModel):
    """Request body for submitting exhibit feedback."""

    exhibit_id: str
    liked: bool
    comment: str = ""


class PlanRequest(BaseModel):
    """Request body to plan a new visit."""

    display_name: str = Field(min_length=1, max_length=100)
    interests: list[str] = Field(min_length=1)
    time_budget_minutes: int = Field(ge=5, le=600)
    accessibility_needs: list[str] = Field(default_factory=list)
    language: str = "en"
    commentary_length: str = "medium"
    memory_mode: str = "persistent"
    visitor_id: str | None = None


class ReplanRequest(BaseModel):
    """Request body for crowd-aware replanning."""

    busy_gallery_id: str
