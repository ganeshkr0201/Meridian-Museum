"""
Evaluation Service — runs the eight visitor profiles and generates metrics.
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from app.models.evaluation import EvaluationReport, ProfileEvalResult
from app.services.visit_service import VisitService
from app.core.logging import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROFILES_FILE = os.path.join(DATA_DIR, "visitor_profiles.json")

INTEREST_TO_TAGS: dict[str, list[str]] = {
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


def _load_exhibit_map() -> dict[str, dict]:
    exhibits_file = os.path.join(DATA_DIR, "exhibits.json")
    with open(exhibits_file, encoding="utf-8") as f:
        data = json.load(f)
    return {e["exhibit_id"]: e for e in data}


def _interest_covered(exhibit: dict, interest: str) -> bool:
    tags = exhibit.get("tags", [])
    relevant_tags = INTEREST_TO_TAGS.get(interest, [interest])
    return any(t in relevant_tags for t in tags)


class EvaluationService:
    def __init__(self, db=None):
        self.visit_service = VisitService(db)

    async def run_evaluation(self) -> EvaluationReport:
        with open(PROFILES_FILE, encoding="utf-8") as f:
            profiles = json.load(f)

        exhibit_map = _load_exhibit_map()
        results: list[ProfileEvalResult] = []

        for profile in profiles:
            logger.info("Evaluating profile: %s", profile["visitor_id"])
            try:
                guide = await self.visit_service.plan_new_visit(profile)
                result = self._evaluate_guide(guide, profile, exhibit_map)
                results.append(result)
            except Exception as e:
                logger.error("Evaluation failed for %s: %s", profile["visitor_id"], e)
                results.append(ProfileEvalResult(
                    visitor_id=profile["visitor_id"],
                    display_name=profile.get("display_name", profile["visitor_id"]),
                    time_budget_minutes=profile.get("time_budget_minutes", 0),
                    total_route_minutes=0.0,
                    time_budget_fit=False,
                    stated_interests=profile.get("interests", []),
                    covered_interests=[],
                    interest_coverage_pct=0.0,
                    num_exhibits_in_route=0,
                    total_walking_minutes=0.0,
                    accessibility_compliant=False,
                    opening_hours_compliant=False,
                ))

        report = self._compile_report(results)
        return report

    def _evaluate_guide(
        self,
        guide,
        profile: dict,
        exhibit_map: dict[str, dict],
    ) -> ProfileEvalResult:
        total_minutes = guide.total_visit_minutes + guide.total_walking_minutes
        time_fit = total_minutes <= profile["time_budget_minutes"]
        stated = profile.get("interests", [])

        covered = []
        for interest in stated:
            for stop in guide.route:
                exhibit = exhibit_map.get(stop.exhibit_id, {})
                if _interest_covered(exhibit, interest):
                    covered.append(interest)
                    break

        coverage_pct = (len(covered) / len(stated) * 100) if stated else 0.0

        # Accessibility compliance: check every stop has accessibility_status == "accessible"
        needs = profile.get("accessibility_needs", [])
        accessibility_compliant = True
        if needs:
            for stop in guide.route:
                if stop.accessibility_status != "accessible":
                    accessibility_compliant = False
                    break

        # Opening hours compliance
        opening_compliant = all(s.opening_status == "open" for s in guide.route)

        return ProfileEvalResult(
            visitor_id=profile["visitor_id"],
            display_name=profile.get("display_name", profile["visitor_id"]),
            time_budget_minutes=profile["time_budget_minutes"],
            total_route_minutes=round(total_minutes, 2),
            time_budget_fit=time_fit,
            stated_interests=stated,
            covered_interests=covered,
            interest_coverage_pct=round(coverage_pct, 2),
            num_exhibits_in_route=len(guide.route),
            total_walking_minutes=round(guide.total_walking_minutes, 2),
            accessibility_compliant=accessibility_compliant,
            opening_hours_compliant=opening_compliant,
        )

    def _compile_report(self, results: list[ProfileEvalResult]) -> EvaluationReport:
        n = len(results) or 1
        fit_count = sum(1 for r in results if r.time_budget_fit)
        avg_coverage = sum(r.interest_coverage_pct for r in results) / n
        avg_exhibits = sum(r.num_exhibits_in_route for r in results) / n
        avg_walking = sum(r.total_walking_minutes for r in results) / n
        acc_count = sum(1 for r in results if r.accessibility_compliant)
        oh_count = sum(1 for r in results if r.opening_hours_compliant)

        return EvaluationReport(
            run_at=datetime.utcnow(),
            profiles=results,
            time_budget_fit_rate_pct=round(fit_count / n * 100, 2),
            average_interest_coverage_pct=round(avg_coverage, 2),
            average_exhibits_per_route=round(avg_exhibits, 2),
            average_walking_minutes=round(avg_walking, 2),
            accessibility_compliance_rate_pct=round(acc_count / n * 100, 2),
            opening_hours_compliance_rate_pct=round(oh_count / n * 100, 2),
            notes="Evaluation run against all eight seeded visitor profiles.",
        )
