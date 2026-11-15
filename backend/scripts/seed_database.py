#!/usr/bin/env python3
"""
Seed the MongoDB database with exhibits, galleries, and visitor profiles.
Run: python scripts/seed_database.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("seed")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "data")


async def seed():
    settings = get_settings()
    try:
        import motor.motor_asyncio
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.mongodb_db_name]
        logger.info("Connected to MongoDB at %s", settings.mongodb_url)
    except Exception as e:
        logger.warning("MongoDB unavailable (%s). Seed data loaded only in-memory during app run.", e)
        return

    for fname, collection in [
        ("exhibits.json", "exhibits"),
        ("galleries.json", "galleries"),
        ("visitor_profiles.json", "visitor_memory"),
    ]:
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        await db[collection].delete_many({})
        if data:
            await db[collection].insert_many(data)
        logger.info("Seeded %d documents into '%s'.", len(data), collection)

    logger.info("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
