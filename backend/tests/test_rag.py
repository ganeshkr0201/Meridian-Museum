"""Tests for RAG chunking, ingestion, and retrieval."""
import pytest
import os
from app.rag.chunking import chunk_curator_note, chunk_catalogue_entry
from app.rag.embeddings import embed_texts, embed_query
from app.rag.ingestion import ingest_all
from app.rag.retriever import retrieve_evidence, retrieve_for_exhibit


DATA_DIR = os.path.join(os.path.dirname(__file__), "../app/data")


def test_chunk_curator_note():
    note_path = os.path.join(DATA_DIR, "curator_notes", "CN-E01-01.txt")
    chunks = chunk_curator_note(note_path)
    assert len(chunks) > 0
    for c in chunks:
        assert c.exhibit_id == "E01"
        assert len(c.text) > 10
        assert c.source_type == "curator_note"


def test_chunk_catalogue_entry():
    entry = {
        "exhibit_id": "E01",
        "title": "Test Exhibit",
        "description": "A long description of the exhibit. It covers many topics.",
        "tags": ["ancient_history"],
        "catalogue_source_id": "CAT-E01",
    }
    chunks = chunk_catalogue_entry(entry)
    assert len(chunks) > 0
    assert chunks[0].exhibit_id == "E01"


def test_embed_texts_returns_correct_dim():
    embeddings = embed_texts(["test text", "another text"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384


def test_embed_query():
    emb = embed_query("ancient history coins")
    assert len(emb) == 384


def test_ingest_all_runs():
    total = ingest_all(force=True)
    assert total > 0


def test_retrieve_evidence_returns_results():
    ingest_all(force=False)
    results = retrieve_evidence(["ancient_history"], top_k=3)
    assert len(results) > 0
    for r in results:
        assert 0.0 <= r.relevance_score <= 1.0
        assert len(r.chunk_text) > 0


def test_retrieve_for_exhibit():
    ingest_all(force=False)
    results = retrieve_for_exhibit("E01", top_k=2)
    # Should return evidence specifically for E01
    for r in results:
        assert r.exhibit_id == "E01"
