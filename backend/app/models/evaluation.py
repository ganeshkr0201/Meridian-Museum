"""Pydantic models for evaluation runner and reports."""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class ProfileEvalResult(BaseModel):
    """Evaluation result for a single visitor profile."""

    visitor_id: str
    display_name: str
    time_budget_minutes: int
    total_route_minutes: float
    time_budget_fit: bool
    stated_interests: list[str]
    covered_interests: list[str]
    interest_coverage_pct: float
    num_exhibits_in_route: int
    total_walking_minutes: float
    accessibility_compliant: bool
    opening_hours_compliant: bool


class EvaluationReport(BaseModel):
    """Full evaluation report across all eight profiles."""

    run_at: datetime = Field(default_factory=datetime.utcnow)
    profiles: list[ProfileEvalResult] = Field(default_factory=list)
    time_budget_fit_rate_pct: float = 0.0
    average_interest_coverage_pct: float = 0.0
    average_exhibits_per_route: float = 0.0
    average_walking_minutes: float = 0.0
    accessibility_compliance_rate_pct: float = 0.0
    opening_hours_compliance_rate_pct: float = 0.0
    notes: str = ""
