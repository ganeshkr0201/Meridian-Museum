import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.crowd_status import get_all_crowd_states, set_crowd_state
from app.models.exhibit import CrowdState

router = APIRouter(prefix="/galleries", tags=["galleries"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
GALLERIES_FILE = os.path.join(DATA_DIR, "galleries.json")


def _load():
    with open(GALLERIES_FILE, encoding="utf-8") as f:
        return json.load(f)


@router.get("/crowd")
async def get_crowd_status():
    states = get_all_crowd_states()
    return {gid: s.model_dump() for gid, s in states.items()}


class CrowdUpdate(BaseModel):
    crowd_state: CrowdState


@router.patch("/{gallery_id}/crowd")
async def update_crowd(gallery_id: str, body: CrowdUpdate):
    galleries = _load()
    ids = {g["gallery_id"] for g in galleries}
    if gallery_id not in ids:
        raise HTTPException(status_code=404, detail="Gallery not found.")
    set_crowd_state(gallery_id, body.crowd_state)
    return {"gallery_id": gallery_id, "crowd_state": body.crowd_state.value}


@router.get("")
async def list_galleries():
    galleries = _load()
    states = get_all_crowd_states()
    for g in galleries:
        gid = g["gallery_id"]
        if gid in states:
            g["crowd_state"] = states[gid].crowd_state.value
    return galleries
