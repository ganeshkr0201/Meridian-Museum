"""
Opening Hours Tool
Checks whether a gallery or exhibit is open at a given simulated visit time.
Uses seeded opening-hours data; does not rely on live external services.
"""

from __future__ import annotations
from datetime import time
from pydantic import BaseModel
from app.core.logging import get_logger

logger = get_logger(__name__)

# Seeded opening hours: gallery_id -> (open_time, close_time)
_GALLERY_HOURS: dict[str, tuple[str, str]] = {
    "G01": ("09:00", "17:00"),
    "G02": ("09:00", "17:00"),
    "G03": ("10:00", "16:00"),
    "G04": ("09:00", "17:00"),
}


class OpeningHoursResult(BaseModel):
    gallery_id: str
    is_open: bool
    opens_at: str
    closes_at: str
    visit_time: str
    reason: str


def _parse_time(t: str) -> time:
    h, m = t.split(":")
    return time(int(h), int(m))


def check_opening_hours(
    gallery_id: str,
    visit_time_str: str = "10:00",
) -> OpeningHoursResult:
    """
    Check whether a gallery is open at the given visit time.

    Args:
        gallery_id: The gallery to check.
        visit_time_str: Simulated visit time in HH:MM format (default 10:00).

    Returns:
        OpeningHoursResult with open/closed status and window.
    """
    hours = _GALLERY_HOURS.get(gallery_id)
    if hours is None:
        logger.warning("No opening hours data for gallery %s", gallery_id)
        return OpeningHoursResult(
            gallery_id=gallery_id,
            is_open=False,
            opens_at="Unknown",
            closes_at="Unknown",
            visit_time=visit_time_str,
            reason=f"No opening hours data found for gallery {gallery_id}.",
        )

    opens_at, closes_at = hours
    visit_t = _parse_time(visit_time_str)
    open_t = _parse_time(opens_at)
    close_t = _parse_time(closes_at)
    is_open = open_t <= visit_t < close_t

    reason = (
        f"Gallery is open {opens_at}–{closes_at}; visit at {visit_time_str} fits."
        if is_open
        else f"Gallery is open {opens_at}–{closes_at}; visit at {visit_time_str} is outside hours."
    )

    logger.debug("Opening hours check: %s at %s → %s", gallery_id, visit_time_str, is_open)
    return OpeningHoursResult(
        gallery_id=gallery_id,
        is_open=is_open,
        opens_at=opens_at,
        closes_at=closes_at,
        visit_time=visit_time_str,
        reason=reason,
    )


def gallery_visit_fits(
    gallery_id: str,
    arrival_offset_minutes: float,
    visit_duration_minutes: int,
    start_time_str: str = "10:00",
) -> tuple[bool, str]:
    """
    Check whether a full visit (arrival + duration) fits within opening hours.

    Args:
        gallery_id: The gallery to check.
        arrival_offset_minutes: Minutes after start_time_str when visitor arrives.
        visit_duration_minutes: How long the visitor will spend.
        start_time_str: When the visitor started their museum trip.

    Returns:
        (fits: bool, reason: str)
    """
    hours = _GALLERY_HOURS.get(gallery_id)
    if hours is None:
        return False, f"No opening hours data for {gallery_id}."

    opens_at_str, closes_at_str = hours
    start_h, start_m = map(int, start_time_str.split(":"))
    start_minutes = start_h * 60 + start_m
    arrival_minutes = start_minutes + arrival_offset_minutes
    departure_minutes = arrival_minutes + visit_duration_minutes

    opens_minutes = sum(int(x) * m for x, m in zip(opens_at_str.split(":"), [60, 1]))
    closes_minutes = sum(int(x) * m for x, m in zip(closes_at_str.split(":"), [60, 1]))

    if arrival_minutes < opens_minutes:
        return False, f"Gallery {gallery_id} not yet open at scheduled arrival."
    if departure_minutes > closes_minutes:
        return False, f"Visit to {gallery_id} extends past closing time {closes_at_str}."
    return True, f"Visit to {gallery_id} fits within opening hours {opens_at_str}–{closes_at_str}."
