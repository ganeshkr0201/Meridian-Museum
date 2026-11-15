"""
Agent C — Route Planner Agent
Plans an ordered visit route that maximises weighted interest coverage
within the visitor's time budget using a heuristic scoring function.
Uses the Walking Distance Tool, Opening Hours Tool, and Crowd Status Tool.
"""

from __future__ import annotations
import json
import os
from app.agents.contracts import RoutePlannerAgentInput, RoutePlannerAgentOutput
from app.models.exhibit import RouteStop, SkippedItem, CrowdState, AccessibilityFeature
from app.models.visitor import AccessibilityNeed
from app.tools.walking_distance import get_walking_distance
from app.tools.opening_hours import gallery_visit_fits
from app.tools.crowd_status import get_crowd_status, get_all_crowd_states
from app.core.logging import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")
GALLERIES_FILE = os.path.join(DATA_DIR, "galleries.json")

# Scoring weights
W_INTEREST = 3.0
W_WALK_PENALTY = 0.5   # per minute of walking
W_CROWD_PENALTY = 0.4  # per penalty minute
W_CURATOR_PRIORITY = 0.5

# Map exhibit tags to interest categories
TAG_TO_INTEREST: dict[str, list[str]] = {
    "ancient_history": ["ancient_history", "archaeology"],
    "archaeology": ["ancient_history", "archaeology"],
    "science": ["science", "technology"],
    "technology": ["science", "technology"],
    "art": ["art", "local_culture"],
    "textiles": ["textiles", "regional_craft"],
    "coins": ["coins", "ancient_history"],
    "local_culture": ["local_culture", "art"],
    "natural_history": ["natural_history"],
    "regional_craft": ["regional_craft", "local_culture"],
}


def _load_exhibits() -> list[dict]:
    with open(EXHIBITS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _load_galleries() -> dict[str, dict]:
    with open(GALLERIES_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    return {g["gallery_id"]: g for g in raw}


def _is_accessible(exhibit: dict, needs: list[str]) -> bool:
    features = [f.lower() for f in exhibit.get("accessibility_features", [])]
    if "wheelchair" in needs or "step_free" in needs:
        if "stairs_required" in features:
            return False
        if "wheelchair_accessible" not in features and "step_free" not in features:
            return False
    if "avoid_stairs" in needs:
        if "stairs_required" in features:
            return False
    return True


def _interest_score(exhibit: dict, interest_weights: dict[str, float]) -> float:
    score = 0.0
    for tag in exhibit.get("tags", []):
        mapped = TAG_TO_INTEREST.get(tag, [tag])
        for interest in mapped:
            score += interest_weights.get(interest, 0.0)
    return score


class RoutePlannerAgent:
    """
    Heuristic route planner.
    Scores each candidate exhibit and greedily selects stops in
    decreasing score order while checking time budget, opening hours,
    accessibility, and crowd status.
    """

    name = "RoutePlannerAgent"

    async def run(self, input_data: RoutePlannerAgentInput) -> RoutePlannerAgentOutput:
        logger.info("[%s] Planning route for %d candidates, budget=%dm",
                    self.name, len(input_data.candidate_exhibit_ids), input_data.visitor_profile.time_budget_minutes)

        exhibits = _load_exhibits()
        galleries = _load_galleries()
        exhibit_map = {e["exhibit_id"]: e for e in exhibits}
        gallery_map = galleries

        needs = [a.value for a in input_data.visitor_profile.accessibility_needs]
        accessible_mode = any(n in needs for n in ("wheelchair", "step_free", "avoid_stairs", "reduced_walking"))
        interest_weights = input_data.visitor_profile.interest_weights

        # Busy galleries: combine crowd tool data with explicit busy list
        all_crowd = get_all_crowd_states()
        busy_gallery_ids = set(input_data.busy_gallery_ids)
        for gid, status in all_crowd.items():
            if status.crowd_state in (CrowdState.BUSY, CrowdState.CLOSED):
                busy_gallery_ids.add(gid)

        completed_ids = set(input_data.completed_exhibit_ids)
        remaining_budget = input_data.visitor_profile.time_budget_minutes - input_data.elapsed_minutes
        warnings: list[str] = []

        # Score all candidates
        scored: list[tuple[float, dict]] = []
        skipped_items: list[SkippedItem] = []

        for eid in input_data.candidate_exhibit_ids:
            exhibit = exhibit_map.get(eid)
            if not exhibit:
                continue
            if eid in completed_ids:
                continue

            gid = exhibit["gallery_id"]
            gallery = gallery_map.get(gid, {})

            # Accessibility check
            if not _is_accessible(exhibit, needs):
                skipped_items.append(SkippedItem(
                    exhibit_id=eid,
                    title=exhibit["title"],
                    reason_code="ACCESSIBILITY",
                    human_readable_reason="Exhibit skipped: does not meet visitor accessibility requirements.",
                ))
                continue

            # Busy/closed gallery check
            if gid in busy_gallery_ids:
                crowd = get_crowd_status(gid)
                skipped_items.append(SkippedItem(
                    exhibit_id=eid,
                    title=exhibit["title"],
                    reason_code="GALLERY_BUSY" if crowd.crowd_state != CrowdState.CLOSED else "GALLERY_CLOSED",
                    human_readable_reason=f"Gallery {gallery.get('name', gid)} is {crowd.crowd_state.value}.",
                ))
                continue

            # Closed exhibit check
            if not exhibit.get("is_open", True):
                skipped_items.append(SkippedItem(
                    exhibit_id=eid,
                    title=exhibit["title"],
                    reason_code="EXHIBIT_CLOSED",
                    human_readable_reason="Exhibit is currently closed.",
                ))
                continue

            crowd_penalty = get_crowd_status(gid).penalty_minutes
            interest_sc = _interest_score(exhibit, interest_weights)
            walk_penalty = 1.0  # placeholder; recalculated when ordering
            score = (W_INTEREST * interest_sc) - (W_CROWD_PENALTY * crowd_penalty) - walk_penalty
            scored.append((score, exhibit))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Greedy time-budget-aware route building
        route: list[RouteStop] = []
        current_gallery = None
        elapsed = input_data.elapsed_minutes
        seq = 1

        for _, exhibit in scored:
            eid = exhibit["exhibit_id"]
            gid = exhibit["gallery_id"]
            gallery = gallery_map.get(gid, {})
            visit_min = exhibit["estimated_visit_minutes"]

            # Walking from current gallery
            if current_gallery and current_gallery != gid:
                walk_result = get_walking_distance(current_gallery, gid, accessible_mode)
                walk_m = walk_result.distance_m
                walk_min = walk_result.walk_minutes
            else:
                walk_m = 0.0
                walk_min = 0.0

            crowd_pen = get_crowd_status(gid).penalty_minutes
            total_stop_time = walk_min + visit_min + crowd_pen

            if elapsed + total_stop_time > remaining_budget + 5:  # 5-min grace
                skipped_items.append(SkippedItem(
                    exhibit_id=eid,
                    title=exhibit["title"],
                    reason_code="TIME_BUDGET",
                    human_readable_reason=f"Skipped: adding this stop would exceed the {input_data.visitor_profile.time_budget_minutes}-minute time budget.",
                ))
                continue

            # Opening hours check
            fits, oh_reason = gallery_visit_fits(
                gid, elapsed + walk_min, visit_min, input_data.start_time
            )
            if not fits:
                skipped_items.append(SkippedItem(
                    exhibit_id=eid,
                    title=exhibit["title"],
                    reason_code="OPENING_HOURS",
                    human_readable_reason=oh_reason,
                ))
                continue

            route.append(RouteStop(
                sequence=seq,
                exhibit_id=eid,
                exhibit_title=exhibit["title"],
                gallery_id=gid,
                gallery_name=gallery.get("name", gid),
                visit_duration_minutes=visit_min,
                walking_distance_from_previous_m=round(walk_m, 1),
                walking_time_from_previous_minutes=round(walk_min, 2),
                planned_arrival_offset_minutes=round(elapsed + walk_min, 2),
                accessibility_status="accessible" if _is_accessible(exhibit, needs) else "inaccessible",
                opening_status="open",
            ))

            elapsed += total_stop_time
            current_gallery = gid
            seq += 1

        total_visit = sum(s.visit_duration_minutes for s in route)
        total_walk = sum(s.walking_time_from_previous_minutes for s in route)
        total_dist = sum(s.walking_distance_from_previous_m for s in route)
        budget_fit = (total_visit + total_walk) <= input_data.visitor_profile.time_budget_minutes

        logger.info("[%s] Route built: %d stops, %.1f min, budget_fit=%s",
                    self.name, len(route), total_visit + total_walk, budget_fit)

        return RoutePlannerAgentOutput(
            route=route,
            skipped_items=skipped_items,
            total_visit_minutes=round(total_visit, 2),
            total_walking_minutes=round(total_walk, 2),
            total_walking_distance_m=round(total_dist, 1),
            time_budget_fit=budget_fit,
            warnings=warnings,
        )
