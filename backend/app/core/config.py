"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    """All application settings resolved from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "museum_guide"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # LLM
    llm_mode: Literal["demo", "openai"] = "demo"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # CORS
    frontend_url: str = "http://localhost:5173"

    # Security
    secret_key: str = "change-me-in-production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
