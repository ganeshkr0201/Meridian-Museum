#!/usr/bin/env python3
"""
Ingest curator notes and exhibit catalogue into ChromaDB.
Run: python scripts/ingest_catalogue.py [--force]
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logging import configure_logging, get_logger
from app.rag.ingestion import ingest_all

configure_logging()
logger = get_logger("ingest")

if __name__ == "__main__":
    force = "--force" in sys.argv
    logger.info("Starting RAG ingestion (force=%s)…", force)
    total = ingest_all(force=force)
    logger.info("Done. %d chunks in ChromaDB.", total)
