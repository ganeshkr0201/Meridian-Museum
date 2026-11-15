import json
import os
from fastapi import APIRouter, Depends
from app.services.evaluation_service import EvaluationService
from app.api.deps import get_evaluation_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

REPORT_DIR = os.path.join(os.path.dirname(__file__), "../../../../evaluation_reports")


@router.post("/run")
async def run_evaluation(service: EvaluationService = Depends(get_evaluation_service)):
    report = await service.run_evaluation()

    # Persist report
    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = report.run_at.strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(REPORT_DIR, f"report_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, default=str)

    return report.model_dump(mode="json")


@router.get("/latest")
async def latest_report():
    os.makedirs(REPORT_DIR, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(REPORT_DIR) if f.endswith(".json")],
        reverse=True,
    )
    if not files:
        return {"message": "No evaluation reports found. Run POST /api/evaluation/run first."}
    with open(os.path.join(REPORT_DIR, files[0]), encoding="utf-8") as f:
        return json.load(f)


@router.get("/profiles")
async def list_profiles():
    profiles_file = os.path.join(
        os.path.dirname(__file__), "../../data/visitor_profiles.json"
    )
    with open(profiles_file, encoding="utf-8") as f:
        return json.load(f)
