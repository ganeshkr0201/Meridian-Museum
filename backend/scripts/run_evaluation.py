#!/usr/bin/env python3
"""
Run evaluation across all eight visitor profiles and write reports.
Run: python scripts/run_evaluation.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logging import configure_logging, get_logger
from app.services.evaluation_service import EvaluationService
from app.rag.ingestion import ingest_all

configure_logging()
logger = get_logger("evaluation")

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "evaluation_reports")


async def main():
    logger.info("Pre-loading RAG index…")
    ingest_all(force=False)

    service = EvaluationService(db=None)
    logger.info("Running evaluation for all 8 visitor profiles…")
    report = await service.run_evaluation()

    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = report.run_at.strftime("%Y%m%d_%H%M%S")

    # JSON report
    json_path = os.path.join(REPORT_DIR, f"report_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, default=str)
    logger.info("JSON report saved: %s", json_path)

    # Human-readable Markdown report
    md_path = os.path.join(REPORT_DIR, f"report_{ts}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Evaluation Report — {report.run_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Time Budget Fit Rate:** {report.time_budget_fit_rate_pct:.1f}%\n\n")
        f.write(f"**Average Interest Coverage:** {report.average_interest_coverage_pct:.1f}%\n\n")
        f.write(f"**Average Exhibits per Route:** {report.average_exhibits_per_route:.1f}\n\n")
        f.write(f"**Average Walking Time:** {report.average_walking_minutes:.1f} min\n\n")
        f.write(f"**Accessibility Compliance:** {report.accessibility_compliance_rate_pct:.1f}%\n\n")
        f.write(f"**Opening Hours Compliance:** {report.opening_hours_compliance_rate_pct:.1f}%\n\n")
        f.write("## Per-Profile Results\n\n")
        f.write("| Visitor | Budget (min) | Route (min) | Budget Fit | Interests | Covered | Coverage % | Exhibits |\n")
        f.write("|---------|-------------|-------------|------------|-----------|---------|-----------|----------|\n")
        for p in report.profiles:
            covered_str = ", ".join(p.covered_interests) if p.covered_interests else "—"
            f.write(
                f"| {p.display_name} | {p.time_budget_minutes} | {p.total_route_minutes:.1f} "
                f"| {'✓' if p.time_budget_fit else '✗'} "
                f"| {', '.join(p.stated_interests)} | {covered_str} "
                f"| {p.interest_coverage_pct:.1f}% | {p.num_exhibits_in_route} |\n"
            )
    logger.info("Markdown report saved: %s", md_path)

    # Print summary to stdout
    print("\n========== EVALUATION SUMMARY ==========")
    print(f"Run at:                  {report.run_at}")
    print(f"Time budget fit rate:    {report.time_budget_fit_rate_pct:.1f}%")
    print(f"Avg interest coverage:   {report.average_interest_coverage_pct:.1f}%")
    print(f"Avg exhibits per route:  {report.average_exhibits_per_route:.1f}")
    print(f"Avg walking time:        {report.average_walking_minutes:.1f} min")
    print(f"Accessibility rate:      {report.accessibility_compliance_rate_pct:.1f}%")
    print("=========================================")


if __name__ == "__main__":
    asyncio.run(main())
