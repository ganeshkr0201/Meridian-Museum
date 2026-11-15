"""
Embedding model wrapper.
Uses sentence-transformers locally by default.
Falls back to a simple keyword hash in demo mode if the model is unavailable.
"""

from __future__ import annotations
import hashlib
import math
from functools import lru_cache
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_model():
    settings = get_settings()
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s", settings.embedding_model)
        model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded.")
        return model
    except Exception as e:
        logger.warning("Could not load sentence-transformers model: %s. Using hash fallback.", e)
        return None


def _hash_embed(text: str, dim: int = 384) -> list[float]:
    """Deterministic pseudo-embedding based on character n-gram hashes (demo fallback)."""
    vec = [0.0] * dim
    for i, ch in enumerate(text[:512]):
        h = int(hashlib.md5(f"{i}{ch}".encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    # L2 normalise
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return embeddings for a list of texts."""
    model = _load_model()
    if model is not None:
        embeddings = model.encode(texts, show_progress_bar=False)
        return [e.tolist() for e in embeddings]
    # Demo fallback
    return [_hash_embed(t) for t in texts]


def embed_query(query: str) -> list[float]:
    """Return embedding for a single query string."""
    return embed_texts([query])[0]
