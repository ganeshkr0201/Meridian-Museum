# Evaluation Methodology

## Overview

The evaluation runner (`scripts/run_evaluation.py`) executes the full five-agent planning workflow for all eight seeded visitor profiles and computes objective metrics from the actual generated routes.

No results are fabricated. The metrics shown in the report are computed from the routes actually produced by the system.

## Eight Visitor Profiles

| ID | Name | Budget | Interests | Accessibility |
|---|---|---|---|---|
| visitor_01 | Aryan | 60 min | ancient_history, archaeology | None |
| visitor_02 | Priya | 45 min | art, local_culture | None |
| visitor_03 | Dev | 50 min | science, technology | None |
| visitor_04 | Nisha | 35 min | natural_history | None |
| visitor_05 | Rahul | 90 min | ancient_history, science, natural_history, art | None |
| visitor_06 | Meera | 30 min | ancient_history, coins | reduced_walking |
| visitor_07 | Anjali | 60 min | art, textiles, regional_craft, local_culture | wheelchair, step_free |
| visitor_08 | Ravi | 40 min | science, ancient_history, natural_history | avoid_stairs, seating_breaks |

## Metric A — Time Budget Fit Rate

**Formula:** (number of profiles where total_route_minutes ≤ time_budget_minutes) / 8 × 100

`total_route_minutes` = `total_visit_minutes` + `total_walking_minutes`

Computed server-side by GuideManagerAgent; the evaluation service reads this directly.

## Metric B — Interest Coverage Rate

For each profile, the evaluator checks whether at least one selected exhibit covers each stated interest category.

**Coverage mapping (interest → relevant exhibit tags):**
- ancient_history → ["ancient_history", "archaeology"]
- science → ["science", "technology"]
- art → ["art", "local_culture"]
- textiles → ["textiles", "regional_craft"]
- coins → ["coins", "ancient_history"]
- natural_history → ["natural_history"]
- etc.

An interest is covered if any stop's exhibit has at least one matching tag. Per-profile percentage = covered / stated × 100. Report shows per-profile and average.

## Metric C — Accessibility Compliance Rate

For profiles with accessibility_needs, every route stop must have `accessibility_status == "accessible"`. Rate = compliant profiles / 8 × 100.

## Metric D — Opening Hours Compliance Rate

Every stop must have `opening_status == "open"`. Rate = compliant profiles / 8 × 100.

## Output Files

Generated in `evaluation_reports/`:
- `report_<timestamp>.json` — full machine-readable EvaluationReport
- `report_<timestamp>.md` — human-readable table

The frontend Evaluation Dashboard reads from `GET /api/evaluation/latest` and displays the same numbers.

## Limitations

- The RAG retriever returns a fixed top-k (12) candidates. Very broad interest sets may return candidates that are semantically similar but not perfectly tag-matched, reducing coverage for edge cases.
- The 5-minute grace in the route planner means routes can exceed budget by up to 5 minutes; routes within this grace are still counted as fit by the evaluator.
