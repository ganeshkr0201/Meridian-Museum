"""
Document chunking for curator notes and exhibit catalogue entries.
Splits long text into meaningful chunks with metadata attached.
"""

from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    chunk_id: str
    source_id: str
    exhibit_id: str
    source_title: str
    source_type: str  # "curator_note" or "catalogue"
    text: str
    metadata: dict


def chunk_curator_note(filepath: str) -> list[TextChunk]:
    """
    Read a curator note file and split into sentence-level chunks.
    Extracts SOURCE_ID, EXHIBIT_ID, and TITLE from the file header.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # Extract header fields
    source_id = _extract_field(raw, "SOURCE_ID") or "UNKNOWN"
    exhibit_id = _extract_field(raw, "EXHIBIT_ID") or "UNKNOWN"
    title = _extract_field(raw, "TITLE") or "Untitled"

    # Remove header lines (lines starting with known keys)
    body_lines = [
        line for line in raw.splitlines()
        if not any(line.startswith(k) for k in ("SOURCE_ID:", "EXHIBIT_ID:", "TITLE:", "AUTHOR:", "COLLECTION:"))
    ]
    body = " ".join(body_lines).strip()

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', body)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    # Group into chunks of ~2-3 sentences (≈120 words)
    chunks: list[TextChunk] = []
    window = 2
    for i in range(0, len(sentences), window):
        chunk_text = " ".join(sentences[i:i + window])
        chunk_id = f"{source_id}-chunk-{i // window + 1}"
        chunks.append(TextChunk(
            chunk_id=chunk_id,
            source_id=source_id,
            exhibit_id=exhibit_id,
            source_title=title,
            source_type="curator_note",
            text=chunk_text,
            metadata={
                "source_id": source_id,
                "exhibit_id": exhibit_id,
                "source_type": "curator_note",
                "title": title,
            },
        ))
    return chunks


def chunk_catalogue_entry(entry: dict) -> list[TextChunk]:
    """
    Turn a single exhibit catalogue dict into text chunks.
    """
    exhibit_id = entry.get("exhibit_id", "UNKNOWN")
    source_id = entry.get("catalogue_source_id", f"CAT-{exhibit_id}")
    title = entry.get("title", "Untitled Exhibit")
    description = entry.get("description", "")
    tags = ", ".join(entry.get("tags", []))

    full_text = f"{title}. {description} Topics: {tags}."

    # Split long descriptions into 2-sentence windows
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    chunks: list[TextChunk] = []
    window = 2
    for i in range(0, len(sentences), window):
        chunk_text = " ".join(sentences[i:i + window])
        chunk_id = f"{source_id}-chunk-{i // window + 1}"
        chunks.append(TextChunk(
            chunk_id=chunk_id,
            source_id=source_id,
            exhibit_id=exhibit_id,
            source_title=f"Catalogue: {title}",
            source_type="catalogue",
            text=chunk_text,
            metadata={
                "source_id": source_id,
                "exhibit_id": exhibit_id,
                "source_type": "catalogue",
                "title": title,
                "tags": tags,
            },
        ))
    return chunks


def _extract_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""
