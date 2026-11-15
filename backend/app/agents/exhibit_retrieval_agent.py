"""
Agent B — Exhibit Retrieval Agent
Performs RAG over the museum exhibit catalogue and curator notes.
Returns relevant evidence chunks and candidate exhibit IDs.
"""

from __future__ import annotations
import json
import os
from app.agents.contracts import ExhibitRetrievalAgentInput, ExhibitRetrievalAgentOutput
from app.models.exhibit import RetrievedEvidence
from app.rag.retriever import retrieve_evidence
from app.rag.ingestion import ingest_all
from app.core.logging import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")


def _load_exhibits() -> list[dict]:
    with open(EXHIBITS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Map interest category → exhibit tags
INTEREST_TO_TAGS: dict[str, list[str]] = {
    "ancient_history": ["ancient_history", "archaeology"],
    "archaeology": ["archaeology", "ancient_history"],
    "science": ["science", "technology"],
    "technology": ["technology", "science"],
    "art": ["art", "local_culture"],
    "textiles": ["textiles", "regional_craft"],
    "coins": ["coins", "ancient_history"],
    "local_culture": ["local_culture", "art", "regional_craft"],
    "natural_history": ["natural_history"],
    "regional_craft": ["regional_craft", "local_culture"],
}


class ExhibitRetrievalAgent:
    """
    Retrieves exhibit evidence from ChromaDB using semantic search.
    Falls back to metadata-based tag filtering in demo mode.
    """

    name = "ExhibitRetrievalAgent"

    async def run(self, input_data: ExhibitRetrievalAgentInput) -> ExhibitRetrievalAgentOutput:
        logger.info("[%s] Retrieving for interests: %s",
                    self.name, [i.value for i in input_data.visitor_profile.interests])
        warnings: list[str] = []

        interests = [i.value for i in input_data.visitor_profile.interests]

        # Ensure ChromaDB is populated
        try:
            ingest_all(force=False)
        except Exception as e:
            logger.warning("[%s] Ingestion check failed: %s", self.name, e)

        # Semantic retrieval
        evidence: list[RetrievedEvidence] = []
        try:
            evidence = retrieve_evidence(interests=interests, top_k=input_data.top_k)
        except Exception as e:
            logger.warning("[%s] RAG retrieval failed, falling back to tag filter: %s", self.name, e)
            warnings.append("RAG retrieval failed; using tag-based fallback.")

        low_confidence = False

        # Fallback: tag-based candidate selection
        if not evidence:
            exhibits = _load_exhibits()
            relevant_tags: set[str] = set()
            for interest in interests:
                relevant_tags.update(INTEREST_TO_TAGS.get(interest, [interest]))

            for exhibit in exhibits:
                if set(exhibit.get("tags", [])) & relevant_tags:
                    evidence.append(RetrievedEvidence(
                        exhibit_id=exhibit["exhibit_id"],
                        source_id=exhibit.get("catalogue_source_id", ""),
                        source_title=f"Catalogue: {exhibit['title']}",
                        chunk_text=exhibit.get("description", ""),
                        relevance_score=0.5,
                        metadata={"source_type": "catalogue_fallback"},
                    ))
            low_confidence = True
            warnings.append("Used tag-based fallback retrieval (low confidence).")

        # Deduplicate candidate exhibit IDs while preserving order
        seen: set[str] = set()
        candidate_ids: list[str] = []
        for ev in evidence:
            if ev.exhibit_id and ev.exhibit_id not in seen:
                seen.add(ev.exhibit_id)
                candidate_ids.append(ev.exhibit_id)

        logger.info("[%s] Found %d candidates: %s", self.name, len(candidate_ids), candidate_ids)
        return ExhibitRetrievalAgentOutput(
            retrieved_evidence=evidence,
            candidate_exhibit_ids=candidate_ids,
            low_confidence=low_confidence,
            warnings=warnings,
        )
