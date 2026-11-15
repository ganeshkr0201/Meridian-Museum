# RAG Design

## Pipeline Overview

```
Curator Notes (13 .txt files)     Exhibit Catalogue (exhibits.json)
         │                                      │
         ▼                                      ▼
   chunk_curator_note()              chunk_catalogue_entry()
         │                                      │
         └──────────────┬───────────────────────┘
                        ▼
                  TextChunk objects
                  (chunk_id, source_id, exhibit_id,
                   source_title, source_type, text, metadata)
                        │
                        ▼
                  embed_texts()
                  (all-MiniLM-L6-v2, 384 dimensions)
                        │
                        ▼
                  ChromaDB PersistentClient
                  Collection: museum_exhibits
                  Similarity: cosine
                  Total chunks: 61
                        │
                   At query time:
                        │
                  embed_query(interests)
                        │
                        ▼
                  collection.query(top_k)
                        │
                        ▼
                  RetrievedEvidence[]
                  (exhibit_id, source_id, source_title,
                   chunk_text, relevance_score, metadata)
```

## Chunking Strategy

**Curator notes** are split by sentence boundary (regex `(?<=[.!?])\s+`), then grouped into 2-sentence windows. Each chunk inherits SOURCE_ID, EXHIBIT_ID, and TITLE from the file header.

**Catalogue entries** are chunked from the description field (title + description + tags), also in 2-sentence windows.

Minimum chunk length: 20 characters (shorter fragments discarded).

## Embedding Model

`sentence-transformers/all-MiniLM-L6-v2` — a 22M parameter model that produces 384-dimensional sentence embeddings. Runs locally on CPU or Apple Silicon MPS. No API key required.

Fallback: if the model fails to load, a deterministic character n-gram hash embedding is used (demo mode). Retrieval quality degrades but the system remains functional.

## Metadata Filters

Each chunk stores:
- `exhibit_id` — enables `retrieve_for_exhibit()` with `where={"exhibit_id": {"$eq": id}}`
- `source_type` — `"curator_note"` or `"catalogue"`
- `source_id` — human-readable reference used in commentary citations

## Citation Integrity

The Commentary Writer Agent is given only the `RetrievedEvidence` list for the specific exhibit it is writing about. Every generated commentary includes `source_references: list[str]` populated from the `source_id` fields of the top-k chunks. No citations are invented.

## Re-indexing

```bash
python scripts/ingest_catalogue.py --force
# or
curl -X POST http://localhost:8000/api/admin/reindex
```

The `force=True` flag deletes and rebuilds the collection. Without it, existing chunks are preserved (idempotent upsert by chunk_id).
