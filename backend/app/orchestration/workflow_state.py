"""
Shared workflow state for a single visit planning execution.
The orchestrator mutates this object as agents run, providing a
complete audit trail accessible via the /trace endpoint.
"""

from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field
from app.models.visit import WorkflowTraceEntry, AgentStatus


@dataclass
class WorkflowState:
    """Mutable container for orchestration progress."""

    visit_id: str
    visitor_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    status: str = "running"  # running | completed | failed
    trace: list[WorkflowTraceEntry] = field(default_factory=list)
    error: str | None = None

    # Shared outputs passed between agents
    visitor_profile_output: object | None = None
    retrieval_output: object | None = None
    route_output: object | None = None
    commentary_output: object | None = None
    guide: object | None = None

    def start_agent(self, agent_name: str, input_summary: str = "") -> WorkflowTraceEntry:
        entry = WorkflowTraceEntry(
            agent_name=agent_name,
            status=AgentStatus.RUNNING,
            started_at=datetime.utcnow(),
            input_summary=input_summary,
        )
        self.trace.append(entry)
        return entry

    def finish_agent(self, entry: WorkflowTraceEntry, output_summary: str = "", error: str | None = None) -> None:
        entry.completed_at = datetime.utcnow()
        entry.duration_ms = (entry.completed_at - entry.started_at).total_seconds() * 1000
        if error:
            entry.status = AgentStatus.FAILED
            entry.error_message = error
        else:
            entry.status = AgentStatus.COMPLETED
            entry.output_summary = output_summary

    def mark_completed(self) -> None:
        self.finished_at = datetime.utcnow()
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        self.finished_at = datetime.utcnow()
        self.status = "failed"
        self.error = error
