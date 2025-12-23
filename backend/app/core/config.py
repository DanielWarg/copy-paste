"""
Core configuration and settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Ollama configuration
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "ministral:3b"
    
    # OpenAI configuration
    openai_api_key: Optional[str] = None
    
    # Server configuration
    backend_port: int = 8000
    frontend_port: int = 3000
    
    # Privacy settings
    mapping_ttl_seconds: int = 900  # 15 minutes
    
    class Config:
        env_file = [".env", "../.env", "../../.env"]  # Check backend/.env, root/.env, and parent
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

