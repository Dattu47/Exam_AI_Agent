"""
Application configuration and environment settings.
Central place for all configurable parameters.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys & Secrets
    GEMINI_API_KEY: str = Field(default="", description="Model API key for Gemini")
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_KEY: str = Field(default="", description="Supabase API key")

    # LLM Configuration
    LLM_MODEL: str = Field(default="gemini-2.0-flash", description="Model name for Gemini LLM")
    LLM_TIMEOUT: int = Field(default=60, description="Timeout in seconds for LLM calls")
    LLM_TEMPERATURE: float = Field(default=0.1, description="Sampling temperature for LLM")

    # Search & Scraping
    MAX_SEARCH_RESULTS: int = Field(default=8, description="Max results per search query")
    MAX_SCRAPE_PAGES: int = Field(default=5, description="Max pages to scrape per search query")
    REQUEST_TIMEOUT: int = Field(default=10, description="HTTP request timeout in seconds")
    SCRAPER_MAX_WORKERS: int = Field(default=6, description="Max parallel threads for scraping")
    USER_AGENT: str = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        description="User-Agent for web requests",
    )

    # Vector Store (FAISS)
    VECTOR_STORE_PATH: str = Field(
        default=str(BASE_DIR / "data" / "faiss_index"),
        description="Path to persist FAISS index",
    )
    EMBEDDING_MODEL: str = Field(
        default="models/embedding-001", description="Embedding model name"
    )

    # API
    API_HOST: str = Field(default="0.0.0.0", description="API host to bind")
    API_PORT: int = Field(default=8000, description="API port")
    API_RELOAD: bool = Field(default=True, description="Auto-reload in development")

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR"
    )

    def resolve_gemini_key(self) -> str:
        """Resolve Gemini API key from settings, env, or Streamlit secrets."""
        if self.GEMINI_API_KEY:
            return self.GEMINI_API_KEY
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if env_key:
            return env_key
        try:
            import streamlit as st
            return st.secrets.get("GEMINI_API_KEY", "").strip()
        except Exception:
            return ""

    def resolve_supabase_credentials(self) -> tuple[str, str]:
        """Resolve Supabase URL and Key from settings, env, or Streamlit secrets."""
        url = self.SUPABASE_URL or os.environ.get("SUPABASE_URL", "").strip()
        key = self.SUPABASE_KEY or os.environ.get("SUPABASE_KEY", "").strip()
        if not url or not key:
            try:
                import streamlit as st
                url = url or st.secrets.get("SUPABASE_URL", "").strip()
                key = key or st.secrets.get("SUPABASE_KEY", "").strip()
            except Exception:
                pass
        return url, key


# Singleton settings instance
settings = Settings()
