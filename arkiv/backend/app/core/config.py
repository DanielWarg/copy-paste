"""
Core configuration and settings.

CRITICAL: This module must NEVER block on import.
- No network calls
- No file I/O that can hang
- No circular imports
- Settings() must be fast and deterministic
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables and .env file.
    
    CRITICAL: This class reads env vars and .env file (non-blocking).
    It does NOT initialize clients, make network calls, or do any I/O
    that can block. All that happens in service modules, not here.
    """
    
    # Ollama configuration
    # Default to localhost for local development, host.docker.internal for Docker
    # Can be overridden via OLLAMA_BASE_URL env var
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "ministral-3:14b"
    
    # OpenAI configuration
    openai_api_key: Optional[str] = None
    
    # Server configuration
    backend_port: int = 8000
    frontend_port: int = 3000
    
    # Privacy settings
    mapping_ttl_seconds: int = 900  # 15 minutes
    
    class Config:
        # Read from .env file in project root (parent of backend/)
        # Path: project_root/.env (one level up from backend/app/core/)
        env_file = str(Path(__file__).parent.parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_ignore_empty = True  # Ignore empty values


# CRITICAL: Simple, fast initialization
# pydantic_settings reads .env file synchronously but it's fast (small file)
# Settings() reads environment variables and .env file - should be instant
settings = Settings()

