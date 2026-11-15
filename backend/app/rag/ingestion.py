"""
Document ingestion pipeline.
Loads curator notes and exhibit catalogue, chunks them, embeds, and
stores in ChromaDB.
"""

from __future__ import annotations
import json
import os
from app.rag.chunking import chunk_curator_note, chunk_catalogue_entry, TextChunk
from app.rag.embeddings import embed_texts
from app.rag.vector_store import get_chroma_client, get_or_create_collection, upsert_chunks, collection_count
from app.core.logging import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CURATOR_NOTES_DIR = os.path.join(DATA_DIR, "curator_notes")
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")


def ingest_all(force: bool = False) -> int:
    """
    Ingest all curator notes and catalogue entries into ChromaDB.
    Skips if already indexed unless force=True.

    Returns:
        Number of chunks indexed.
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    if not force and collection_count(collection) > 0:
        logger.info("ChromaDB already has %d chunks. Skipping ingestion (use force=True to re-index).", collection_count(collection))
        return collection_count(collection)

    all_chunks: list[TextChunk] = []

    # 1. Curator notes
    if os.path.isdir(CURATOR_NOTES_DIR):
        for fname in sorted(os.listdir(CURATOR_NOTES_DIR)):
            if fname.endswith(".txt"):
                fpath = os.path.join(CURATOR_NOTES_DIR, fname)
                try:
                    chunks = chunk_curator_note(fpath)
                    all_chunks.extend(chunks)
                    logger.debug("Chunked %s → %d chunks", fname, len(chunks))
                except Exception as e:
                    logger.warning("Failed to chunk %s: %s", fname, e)

    # 2. Exhibit catalogue
    if os.path.isfile(EXHIBITS_FILE):
        with open(EXHIBITS_FILE, "r", encoding="utf-8") as f:
            exhibits = json.load(f)
        for exhibit in exhibits:
            try:
                chunks = chunk_catalogue_entry(exhibit)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning("Failed to chunk exhibit %s: %s", exhibit.get("exhibit_id"), e)

    if not all_chunks:
        logger.warning("No chunks found to ingest.")
        return 0

    # 3. Embed
    texts = [c.text for c in all_chunks]
    logger.info("Embedding %d chunks…", len(all_chunks))
    embeddings = embed_texts(texts)

    # 4. Upsert into ChromaDB
    upsert_chunks(
        collection=collection,
        ids=[c.chunk_id for c in all_chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[c.metadata for c in all_chunks],
    )

    total = collection_count(collection)
    logger.info("Ingestion complete. Total chunks in store: %d", total)
    return total
