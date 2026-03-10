"""
Application configuration and environment settings.
Central place for all configurable parameters.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # LLM Configuration - Ollama by default (run: ollama run llama2)
    LLM_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    LLM_MODEL: str = Field(default="llama2", description="Model name for Ollama (e.g., llama2, mistral)")
    LLM_TIMEOUT: int = Field(default=120, description="Timeout in seconds for LLM calls")

    # Search & Scraping
    MAX_SEARCH_RESULTS: int = Field(default=10, description="Max results per DuckDuckGo search")
    MAX_SCRAPE_PAGES: int = Field(default=5, description="Max pages to scrape per search query")
    REQUEST_TIMEOUT: int = Field(default=15, description="HTTP request timeout in seconds")
    USER_AGENT: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ExamResearchBot/1.0",
        description="User-Agent for web requests"
    )

    # Vector Store (FAISS)
    VECTOR_STORE_PATH: str = Field(
        default=str(BASE_DIR / "data" / "faiss_index"),
        description="Path to persist FAISS index"
    )
    # For Ollama embeddings, use a model that Ollama can pull (default below).
    # If you want HF sentence-transformers embeddings, swap VectorStore implementation accordingly.
    EMBEDDING_MODEL: str = Field(default="nomic-embed-text", description="Embedding model name")

    # API
    API_HOST: str = Field(default="0.0.0.0", description="API host to bind")
    API_PORT: int = Field(default=8000, description="API port")
    API_RELOAD: bool = Field(default=True, description="Auto-reload in development")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton settings instance
settings = Settings()
