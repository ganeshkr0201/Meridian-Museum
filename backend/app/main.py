"""
Museum Exhibit Guide — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.api.routes import health, visitors, visits, exhibits, galleries, evaluation, admin

configure_logging()
settings = get_settings()

app = FastAPI(
    title="Museum Exhibit Guide API",
    description="Multi-agent personalised museum visit guide — Meridian Museum (Fictional Demonstration Dataset)",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(visitors.router, prefix="/api")
app.include_router(visits.router, prefix="/api")
app.include_router(exhibits.router, prefix="/api")
app.include_router(galleries.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.on_event("startup")
async def startup():
    from app.core.logging import get_logger
    logger = get_logger("startup")
    logger.info("Museum Exhibit Guide API starting up (LLM_MODE=%s)", settings.llm_mode)
    # Pre-load RAG index on startup (non-blocking)
    try:
        from app.rag.ingestion import ingest_all
        ingest_all(force=False)
    except Exception as e:
        logger.warning("RAG ingestion on startup failed: %s", e)
