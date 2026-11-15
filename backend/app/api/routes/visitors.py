from fastapi import APIRouter, HTTPException, Depends
from app.memory.visitor_memory import VisitorMemoryService
from app.models.visitor import VisitorMemory
from app.api.deps import get_memory_service

router = APIRouter(prefix="/visitors", tags=["visitors"])


@router.post("", status_code=201)
async def create_visitor(
    body: dict,
    memory: VisitorMemoryService = Depends(get_memory_service),
):
    """Create or update visitor memory."""
    try:
        mem = await memory.create_from_form(
            visitor_id=body.get("visitor_id") or __import__("uuid").uuid4().__str__(),
            display_name=body.get("display_name", "Guest"),
            interests=body.get("interests", []),
            time_budget_minutes=body.get("time_budget_minutes", 60),
            accessibility_needs=body.get("accessibility_needs", []),
            language=body.get("language", "en"),
            commentary_length=body.get("commentary_length", "medium"),
            memory_mode=body.get("memory_mode", "persistent"),
        )
        return mem.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{visitor_id}")
async def get_visitor(
    visitor_id: str,
    memory: VisitorMemoryService = Depends(get_memory_service),
):
    mem = await memory.get_memory(visitor_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Visitor not found.")
    return mem.model_dump()


@router.patch("/{visitor_id}/preferences")
async def update_preferences(
    visitor_id: str,
    body: dict,
    memory: VisitorMemoryService = Depends(get_memory_service),
):
    mem = await memory.update_preferences(visitor_id, body)
    if not mem:
        raise HTTPException(status_code=404, detail="Visitor not found.")
    return mem.model_dump()


@router.delete("/{visitor_id}/memory", status_code=204)
async def clear_memory(
    visitor_id: str,
    memory: VisitorMemoryService = Depends(get_memory_service),
):
    await memory.clear_memory(visitor_id)
