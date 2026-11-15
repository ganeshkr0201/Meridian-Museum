"""
Agent D — Commentary Writer Agent
Generates grounded, visitor-friendly commentary for each route stop.
Uses only evidence returned by the Exhibit Retrieval Agent.
Operates in LLM mode (OpenAI) or deterministic demo mode.
"""

from __future__ import annotations
import json
import os
from app.agents.contracts import CommentaryWriterAgentInput, CommentaryWriterAgentOutput
from app.models.exhibit import ExhibitCommentary, RetrievedEvidence
from app.models.visitor import CommentaryLength
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")


def _load_exhibit_map() -> dict[str, dict]:
    with open(EXHIBITS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return {e["exhibit_id"]: e for e in data}


def _evidence_for_exhibit(exhibit_id: str, evidence: list[RetrievedEvidence]) -> list[RetrievedEvidence]:
    return [e for e in evidence if e.exhibit_id == exhibit_id]


def _interest_match_reason(exhibit: dict, interests: list[str]) -> str:
    tags = exhibit.get("tags", [])
    matched = [i for i in interests if any(i in t or t in i for t in tags)]
    if matched:
        return f"This exhibit connects to your stated interests in {', '.join(matched)}."
    return "This exhibit was selected as part of your personalised route."


def _build_demo_commentary(
    exhibit: dict,
    evidence: list[RetrievedEvidence],
    interests: list[str],
    length: CommentaryLength,
) -> ExhibitCommentary:
    """Build deterministic commentary without calling an LLM."""
    title = exhibit.get("title", "")
    description = exhibit.get("description", "")

    # Use best evidence chunk as the basis
    top_evidence = sorted(evidence, key=lambda e: e.relevance_score, reverse=True)
    source_refs = list({e.source_id for e in top_evidence[:2]})

    if top_evidence:
        evidence_text = top_evidence[0].chunk_text
    else:
        evidence_text = description

    if length == CommentaryLength.SHORT:
        commentary = f"{evidence_text[:200].rstrip()}."
    elif length == CommentaryLength.LONG:
        all_text = " ".join(e.chunk_text for e in top_evidence[:3])
        commentary = f"{all_text[:600].rstrip()}."
    else:
        commentary = f"{evidence_text[:350].rstrip()}."

    did_you_know = ""
    if top_evidence and len(top_evidence) > 1:
        second_chunk = top_evidence[1].chunk_text
        if len(second_chunk) > 40:
            did_you_know = f"Did you know? {second_chunk[:200].rstrip()}."

    return ExhibitCommentary(
        exhibit_id=exhibit["exhibit_id"],
        commentary=commentary,
        interest_match_reason=_interest_match_reason(exhibit, interests),
        source_references=source_refs if source_refs else ["Museum Catalogue"],
        confidence="high" if top_evidence and top_evidence[0].relevance_score > 0.4 else "low",
        did_you_know=did_you_know,
    )


async def _build_llm_commentary(
    exhibit: dict,
    evidence: list[RetrievedEvidence],
    interests: list[str],
    length: CommentaryLength,
) -> ExhibitCommentary:
    """Build commentary using an OpenAI-compatible API."""
    settings = get_settings()
    try:
        import openai
        client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

        evidence_block = "\n".join(f"- [{e.source_id}] {e.chunk_text}" for e in evidence[:4])
        length_instruction = {
            CommentaryLength.SHORT: "2 sentences",
            CommentaryLength.MEDIUM: "3–4 sentences",
            CommentaryLength.LONG: "5–6 sentences",
        }[length]

        prompt = f"""You are a museum guide writing for a visitor interested in: {', '.join(interests)}.

Exhibit: {exhibit.get('title')}
Evidence from the museum catalogue and curator notes:
{evidence_block}

Write a {length_instruction} commentary grounded only in the evidence above.
Then write one sentence explaining why this exhibit matches the visitor's interests.
Do not invent facts not present in the evidence.
Format as JSON: {{"commentary": "...", "interest_match_reason": "...", "did_you_know": "..."}}"""

        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)

        source_refs = list({e.source_id for e in evidence[:3]})
        return ExhibitCommentary(
            exhibit_id=exhibit["exhibit_id"],
            commentary=parsed.get("commentary", ""),
            interest_match_reason=parsed.get("interest_match_reason", ""),
            source_references=source_refs,
            confidence="high",
            did_you_know=parsed.get("did_you_know", ""),
        )
    except Exception as e:
        logger.warning("[CommentaryWriterAgent] LLM call failed for %s: %s. Using demo fallback.", exhibit.get("exhibit_id"), e)
        return _build_demo_commentary(exhibit, evidence, interests, length)


class CommentaryWriterAgent:
    """
    Writes visitor-friendly commentary grounded in retrieved evidence.
    Operates in demo mode (deterministic) or LLM mode (OpenAI).
    """

    name = "CommentaryWriterAgent"

    async def run(self, input_data: CommentaryWriterAgentInput) -> CommentaryWriterAgentOutput:
        settings = get_settings()
        logger.info("[%s] Writing commentary for %d stops", self.name, len(input_data.route))

        exhibit_map = _load_exhibit_map()
        interests = [i.value for i in input_data.visitor_profile.interests]
        length = input_data.visitor_profile.commentary_length
        warnings: list[str] = []
        commentaries: dict[str, ExhibitCommentary] = {}

        for stop in input_data.route:
            eid = stop.exhibit_id
            exhibit = exhibit_map.get(eid)
            if not exhibit:
                warnings.append(f"Exhibit {eid} not found in catalogue; skipping commentary.")
                continue

            evidence = _evidence_for_exhibit(eid, input_data.retrieved_evidence)
            if not evidence:
                warnings.append(f"No retrieved evidence for exhibit {eid}; using description only.")
                # Create minimal evidence from catalogue
                evidence = [RetrievedEvidence(
                    exhibit_id=eid,
                    source_id=exhibit.get("catalogue_source_id", "CAT"),
                    source_title=f"Catalogue: {exhibit['title']}",
                    chunk_text=exhibit.get("description", ""),
                    relevance_score=0.3,
                    metadata={"source_type": "catalogue"},
                )]

            if settings.llm_mode == "openai" and settings.openai_api_key:
                commentary = await _build_llm_commentary(exhibit, evidence, interests, length)
            else:
                commentary = _build_demo_commentary(exhibit, evidence, interests, length)

            commentaries[eid] = commentary

        logger.info("[%s] Commentary complete for %d exhibits", self.name, len(commentaries))
        return CommentaryWriterAgentOutput(commentaries=commentaries, warnings=warnings)
