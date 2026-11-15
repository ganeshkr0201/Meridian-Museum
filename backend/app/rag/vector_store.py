"""
ChromaDB Vector Store wrapper.
Handles collection creation, document upsert, and similarity search.
"""

from __future__ import annotations
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "museum_exhibits"


def get_chroma_client() -> chromadb.PersistentClient:
    settings = get_settings()
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_or_create_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(
    collection: chromadb.Collection,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    logger.info("Upserted %d chunks into ChromaDB collection '%s'.", len(ids), COLLECTION_NAME)


def query_collection(
    collection: chromadb.Collection,
    query_embeddings: list[list[float]],
    n_results: int = 5,
    where: dict | None = None,
) -> dict:
    kwargs: dict = {
        "query_embeddings": query_embeddings,
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def collection_count(collection: chromadb.Collection) -> int:
    return collection.count()
