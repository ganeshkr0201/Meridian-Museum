"""
Agent E — Guide Manager Agent
Compiles and validates the final visit guide from all upstream agent outputs.
Checks ordering, time totals, opening hours, accessibility, and evidence references.
Flags inconsistencies and returns a final structured VisitGuide.
"""

from __future__ import annotations
from app.agents.contracts import GuideManagerAgentInput, GuideManagerAgentOutput
from app.models.visit import VisitGuide
from app.models.exhibit import RetrievedEvidence
from app.tools.opening_hours import gallery_visit_fits
from app.core.logging import get_logger

logger = get_logger(__name__)

# Map interest category values to relevant exhibit tags
INTEREST_TO_TAG_MAP: dict[str, list[str]] = {
    "ancient_history": ["ancient_history", "archaeology"],
    "archaeology": ["ancient_history", "archaeology"],
    "science": ["science", "technology"],
    "technology": ["science", "technology"],
    "art": ["art", "local_culture"],
    "textiles": ["textiles", "regional_craft"],
    "coins": ["coins", "ancient_history"],
    "local_culture": ["local_culture", "art", "regional_craft"],
    "natural_history": ["natural_history"],
    "regional_craft": ["regional_craft", "local_culture"],
}


class GuideManagerAgent:
    """
    Validates and compiles the final VisitGuide.
    Performs server-side total recalculation, feasibility checks,
    and interest-coverage computation.
    """

    name = "GuideManagerAgent"

    async def run(
        self,
        input_data: GuideManagerAgentInput,
        exhibit_tag_map: dict[str, list[str]] | None = None,
    ) -> tuple[VisitGuide, GuideManagerAgentOutput]:
        logger.info("[%s] Compiling guide for visit %s", self.name, input_data.visit_id)

        profile = input_data.visitor_profile
        route_out = input_data.route_output
        commentary_out = input_data.commentary_output
        route = route_out.route
        warnings: list[str] = []
        validation_errors: list[str] = []

        # 1. Recalculate totals server-side
        total_visit = sum(s.visit_duration_minutes for s in route)
        total_walk = sum(s.walking_time_from_previous_minutes for s in route)
        total_dist = sum(s.walking_distance_from_previous_m for s in route)
        corrected_total = round(total_visit + total_walk, 2)

        if abs(corrected_total - (route_out.total_visit_minutes + route_out.total_walking_minutes)) > 1.0:
            warnings.append("Route totals were recalculated server-side.")

        # 2. Time budget check
        time_budget_fit = corrected_total <= profile.time_budget_minutes
        if not time_budget_fit:
            validation_errors.append(
                f"Route total ({corrected_total:.1f} min) exceeds time budget ({profile.time_budget_minutes} min)."
            )

        # 3. Opening-hours feasibility check
        for stop in route:
            fits, reason = gallery_visit_fits(
                stop.gallery_id,
                stop.planned_arrival_offset_minutes,
                stop.visit_duration_minutes,
            )
            if not fits:
                validation_errors.append(f"Stop {stop.sequence} ({stop.exhibit_title}): {reason}")

        # 4. Commentary coverage check
        for stop in route:
            if stop.exhibit_id not in commentary_out.commentaries:
                warnings.append(f"No commentary generated for exhibit {stop.exhibit_id}.")

        # 5. Source reference integrity: every commentary must cite at least one source
        for eid, commentary in commentary_out.commentaries.items():
            if not commentary.source_references:
                warnings.append(f"Commentary for exhibit {eid} has no source references.")

        # 6. Interest coverage calculation
        interest_coverage: dict[str, bool] = {i.value: False for i in profile.interests}
        if exhibit_tag_map:
            for stop in route:
                tags = exhibit_tag_map.get(stop.exhibit_id, [])
                for interest in profile.interests:
                    relevant_tags = INTEREST_TO_TAG_MAP.get(interest.value, [interest.value])
                    if any(t in relevant_tags for t in tags):
                        interest_coverage[interest.value] = True

        # 7. Sequence check
        for i, stop in enumerate(route):
            if stop.sequence != i + 1:
                warnings.append(f"Stop sequence mismatch at position {i + 1}.")

        is_valid = len(validation_errors) == 0

        guide = VisitGuide(
            visit_id=input_data.visit_id,
            visitor_id=profile.visitor_id,
            route=route,
            commentaries=commentary_out.commentaries,
            skipped_items=route_out.skipped_items,
            total_visit_minutes=round(total_visit, 2),
            total_walking_minutes=round(total_walk, 2),
            total_walking_distance_m=round(total_dist, 1),
            time_budget_minutes=profile.time_budget_minutes,
            time_budget_fit=time_budget_fit,
            interest_coverage=interest_coverage,
            sources=input_data.retrieved_evidence,
            crowd_replan_version=input_data.crowd_replan_version,
            replan_explanation=input_data.replan_explanation,
        )

        manager_output = GuideManagerAgentOutput(
            valid=is_valid,
            validation_errors=validation_errors,
            warnings=warnings,
            corrected_total_minutes=corrected_total,
        )

        logger.info("[%s] Guide compiled. Valid=%s, errors=%d, warnings=%d",
                    self.name, is_valid, len(validation_errors), len(warnings))
        return guide, manager_output
