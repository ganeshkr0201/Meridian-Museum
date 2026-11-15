"""Tests for the evaluation service."""
import pytest
from app.services.evaluation_service import EvaluationService
from app.models.evaluation import EvaluationReport


@pytest.mark.asyncio
async def test_evaluation_runs_all_profiles():
    service = EvaluationService(db=None)
    report = await service.run_evaluation()
    assert isinstance(report, EvaluationReport)
    assert len(report.profiles) == 8


@pytest.mark.asyncio
async def test_time_budget_fit_rate_is_percentage():
    service = EvaluationService(db=None)
    report = await service.run_evaluation()
    assert 0.0 <= report.time_budget_fit_rate_pct <= 100.0


@pytest.mark.asyncio
async def test_interest_coverage_per_profile():
    service = EvaluationService(db=None)
    report = await service.run_evaluation()
    for p in report.profiles:
        assert 0.0 <= p.interest_coverage_pct <= 100.0


@pytest.mark.asyncio
async def test_all_profiles_have_results():
    service = EvaluationService(db=None)
    report = await service.run_evaluation()
    ids = {p.visitor_id for p in report.profiles}
    for expected in [f"visitor_0{i}" for i in range(1, 9)]:
        assert expected in ids


@pytest.mark.asyncio
async def test_average_coverage_between_0_and_100():
    service = EvaluationService(db=None)
    report = await service.run_evaluation()
    assert 0.0 <= report.average_interest_coverage_pct <= 100.0
