"""
RAG Retriever
Retrieves relevant text chunks from ChromaDB for a given visitor query.
Returns RetrievedEvidence objects with source provenance.
"""

from __future__ import annotations
from app.rag.embeddings import embed_query
from app.rag.vector_store import get_chroma_client, get_or_create_collection, query_collection
from app.models.exhibit import RetrievedEvidence
from app.core.logging import get_logger

logger = get_logger(__name__)


def retrieve_evidence(
    interests: list[str],
    top_k: int = 8,
    exhibit_ids: list[str] | None = None,
) -> list[RetrievedEvidence]:
    """
    Retrieve top-k evidence chunks most relevant to the visitor's interests.

    Args:
        interests: List of interest category strings.
        top_k: Number of chunks to retrieve.
        exhibit_ids: Optional filter to specific exhibit IDs.

    Returns:
        List of RetrievedEvidence sorted by relevance (highest first).
    """
    query_text = "museum exhibits about " + ", ".join(interests)
    q_embedding = embed_query(query_text)

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty. Run ingestion first.")
        return []

    where_filter = None
    if exhibit_ids:
        where_filter = {"exhibit_id": {"$in": exhibit_ids}}

    try:
        results = query_collection(
            collection=collection,
            query_embeddings=[q_embedding],
            n_results=min(top_k, collection.count()),
            where=where_filter,
        )
    except Exception as e:
        logger.error("ChromaDB query failed: %s", e)
        return []

    evidence_list: list[RetrievedEvidence] = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score 0–1
        score = max(0.0, 1.0 - dist / 2.0)
        evidence_list.append(RetrievedEvidence(
            exhibit_id=meta.get("exhibit_id", ""),
            source_id=meta.get("source_id", ""),
            source_title=meta.get("title", "Unknown Source"),
            chunk_text=doc,
            relevance_score=round(score, 4),
            metadata=meta,
        ))

    evidence_list.sort(key=lambda e: e.relevance_score, reverse=True)
    logger.debug("Retrieved %d evidence chunks for interests: %s", len(evidence_list), interests)
    return evidence_list


def retrieve_for_exhibit(exhibit_id: str, top_k: int = 4) -> list[RetrievedEvidence]:
    """Retrieve evidence chunks specifically for one exhibit."""
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    if collection.count() == 0:
        return []

    q_embedding = embed_query(f"exhibit {exhibit_id} description facts")
    try:
        results = query_collection(
            collection=collection,
            query_embeddings=[q_embedding],
            n_results=min(top_k, collection.count()),
            where={"exhibit_id": {"$eq": exhibit_id}},
        )
    except Exception as e:
        logger.error("ChromaDB exhibit query failed: %s", e)
        return []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        RetrievedEvidence(
            exhibit_id=meta.get("exhibit_id", ""),
            source_id=meta.get("source_id", ""),
            source_title=meta.get("title", ""),
            chunk_text=doc,
            relevance_score=round(max(0.0, 1.0 - d / 2.0), 4),
            metadata=meta,
        )
        for doc, meta, d in zip(docs, metas, distances)
    ]
