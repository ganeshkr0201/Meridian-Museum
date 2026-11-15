from fastapi import APIRouter, HTTPException, Depends
from app.models.visit import PlanRequest, CompletedStop, FeedbackRequest, ReplanRequest
from app.services.visit_service import VisitService
from app.api.deps import get_visit_service

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("/plan")
async def plan_visit(
    body: PlanRequest,
    service: VisitService = Depends(get_visit_service),
):
    try:
        guide = await service.plan_new_visit(body.model_dump())
        return guide.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{visit_id}")
async def get_visit(
    visit_id: str,
    service: VisitService = Depends(get_visit_service),
):
    guide = await service.get_visit(visit_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Visit not found.")
    return guide.model_dump(mode="json")


@router.get("/{visit_id}/trace")
async def get_trace(
    visit_id: str,
    service: VisitService = Depends(get_visit_service),
):
    guide = await service.get_visit(visit_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Visit not found.")
    return {"visit_id": visit_id, "trace": [t.model_dump(mode="json") for t in guide.workflow_trace]}


@router.post("/{visit_id}/complete-stop")
async def complete_stop(
    visit_id: str,
    body: CompletedStop,
    service: VisitService = Depends(get_visit_service),
):
    guide = await service.complete_stop(visit_id, body.exhibit_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Visit not found.")
    return guide.model_dump(mode="json")


@router.post("/{visit_id}/feedback")
async def submit_feedback(
    visit_id: str,
    body: FeedbackRequest,
    service: VisitService = Depends(get_visit_service),
):
    await service.submit_feedback(visit_id, body.exhibit_id, body.liked, body.comment)
    return {"status": "ok"}


@router.post("/{visit_id}/replan")
async def replan_visit(
    visit_id: str,
    body: ReplanRequest,
    service: VisitService = Depends(get_visit_service),
):
    guide = await service.replan(visit_id, body.busy_gallery_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Visit not found.")
    return guide.model_dump(mode="json")


@router.get("/{visit_id}/sources")
async def get_sources(
    visit_id: str,
    service: VisitService = Depends(get_visit_service),
):
    guide = await service.get_visit(visit_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Visit not found.")
    return {"visit_id": visit_id, "sources": [s.model_dump() for s in guide.sources]}
