from fastapi import APIRouter
from app.rag.ingestion import ingest_all

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reindex")
async def reindex():
    """Re-ingest all curator notes and catalogue entries into ChromaDB."""
    total = ingest_all(force=True)
    return {"status": "ok", "chunks_indexed": total}
