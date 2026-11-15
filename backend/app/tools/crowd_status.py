"""
Crowd Status Tool
Returns the current crowd state of a gallery and a crowd penalty score
used by the route planner.
"""

from __future__ import annotations
from pydantic import BaseModel
from app.models.exhibit import CrowdState
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory crowd state store; persisted to DB in the services layer.
# Initialised from seed data on startup.
_CROWD_STATE: dict[str, CrowdState] = {
    "G01": CrowdState.NORMAL,
    "G02": CrowdState.NORMAL,
    "G03": CrowdState.NORMAL,
    "G04": CrowdState.NORMAL,
}

# Penalty minutes added to effective visit time for each crowd level
CROWD_PENALTY: dict[CrowdState, float] = {
    CrowdState.NORMAL: 0.0,
    CrowdState.MODERATE: 3.0,
    CrowdState.BUSY: 8.0,
    CrowdState.CLOSED: 999.0,
}


class CrowdStatusResult(BaseModel):
    gallery_id: str
    crowd_state: CrowdState
    penalty_minutes: float
    is_visitable: bool
    description: str


def get_crowd_status(gallery_id: str) -> CrowdStatusResult:
    """Return the crowd status and time penalty for a gallery."""
    state = _CROWD_STATE.get(gallery_id, CrowdState.NORMAL)
    penalty = CROWD_PENALTY[state]
    is_visitable = state != CrowdState.CLOSED

    descriptions = {
        CrowdState.NORMAL: "Gallery is uncrowded. Expect a comfortable visit.",
        CrowdState.MODERATE: "Gallery is moderately busy. Add a few minutes of queuing.",
        CrowdState.BUSY: "Gallery is busy. Significant wait times expected.",
        CrowdState.CLOSED: "Gallery is currently closed. Cannot be visited.",
    }

    return CrowdStatusResult(
        gallery_id=gallery_id,
        crowd_state=state,
        penalty_minutes=penalty,
        is_visitable=is_visitable,
        description=descriptions[state],
    )


def set_crowd_state(gallery_id: str, state: CrowdState) -> None:
    """Update the crowd state for a gallery (in-memory, mirrored to DB by service)."""
    _CROWD_STATE[gallery_id] = state
    logger.info("Crowd state updated: %s → %s", gallery_id, state.value)


def get_all_crowd_states() -> dict[str, CrowdStatusResult]:
    """Return crowd status for all galleries."""
    return {gid: get_crowd_status(gid) for gid in _CROWD_STATE}


def reset_crowd_states() -> None:
    """Reset all galleries to NORMAL (used by seed/test scripts)."""
    for gid in _CROWD_STATE:
        _CROWD_STATE[gid] = CrowdState.NORMAL
