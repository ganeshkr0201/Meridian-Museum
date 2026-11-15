import json
import os
from fastapi import APIRouter, HTTPException, Query
from app.rag.ingestion import ingest_all

router = APIRouter(prefix="/exhibits", tags=["exhibits"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")


def _load():
    with open(EXHIBITS_FILE, encoding="utf-8") as f:
        return json.load(f)


@router.get("")
async def list_exhibits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    exhibits = _load()
    start = (page - 1) * page_size
    return {
        "total": len(exhibits),
        "page": page,
        "page_size": page_size,
        "items": exhibits[start: start + page_size],
    }


@router.get("/{exhibit_id}")
async def get_exhibit(exhibit_id: str):
    exhibits = _load()
    for e in exhibits:
        if e["exhibit_id"] == exhibit_id:
            return e
    raise HTTPException(status_code=404, detail="Exhibit not found.")
