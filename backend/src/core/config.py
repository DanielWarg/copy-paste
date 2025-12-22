"""
Configuration management with pydantic-settings and security validation
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import os


class Settings(BaseSettings):
    """Application settings with security validation"""
    
    # Public Configuration
    public_base_url: str = Field(
        default="https://nyhetsdesk.postboxen.se",
        alias="PUBLIC_BASE_URL"
    )
    api_key_header: str = Field(
        default="X-API-Key",
        alias="API_KEY_HEADER"
    )
    
    # Ports
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_port: int = Field(default=3000, alias="FRONTEND_PORT")
    
    # Database
    database_url: str = Field(
        default="postgresql+psycopg://copypaste:copypaste@postgres:5432/copypaste",
        alias="DATABASE_URL"
    )
    
    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://ollama:11434",
        alias="OLLAMA_BASE_URL"
    )
    ollama_llm_model: str = Field(
        default="ministral-3:8b",
        alias="OLLAMA_LLM_MODEL"
    )
    ollama_embed_model: str = Field(
        default="nomic-embed-text",
        alias="OLLAMA_EMBED_MODEL"
    )
    
    # Security & Limits
    max_upload_mb: int = Field(default=20, alias="MAX_UPLOAD_MB")
    max_text_chars: int = Field(default=20000, alias="MAX_TEXT_CHARS")
    rate_limit_rpm: int = Field(default=30, alias="RATE_LIMIT_RPM")
    llm_concurrency: int = Field(default=2, alias="LLM_CONCURRENCY")
    
    # Debug
    debug: bool = Field(default=False, alias="DEBUG")
    
    # API Keys (comma-separated)
    api_keys: str = Field(
        default="demo-key-12345,test-key-67890",
        alias="API_KEYS"
    )
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,https://nyhetsdesk.postboxen.se",
        alias="CORS_ORIGINS"
    )
    
    @validator("ollama_base_url")
    def validate_ollama_url(cls, v):
        """
        Block remote Ollama URLs unless explicitly allowed
        
        SECURITY: Ollama has no authentication locally.
        Exposing Ollama to the internet would allow anyone to use it.
        """
        if not v.startswith(("http://localhost", "http://127.0.0.1", "http://ollama", "http://host.docker.internal")):
            if os.getenv("ALLOW_REMOTE_OLLAMA", "false").lower() != "true":
                raise ValueError(
                    "Remote Ollama URLs are blocked for security. "
                    "Ollama has no auth locally. Set ALLOW_REMOTE_OLLAMA=true to override (NOT RECOMMENDED)."
                )
        return v
    
    @validator("max_upload_mb")
    def validate_max_upload(cls, v):
        """Ensure reasonable upload limits"""
        if v < 1 or v > 100:
            raise ValueError("MAX_UPLOAD_MB must be between 1 and 100")
        return v
    
    @validator("rate_limit_rpm")
    def validate_rate_limit(cls, v):
        """Ensure reasonable rate limits"""
        if v < 1 or v > 1000:
            raise ValueError("RATE_LIMIT_RPM must be between 1 and 1000")
        return v
    
    @validator("llm_concurrency")
    def validate_concurrency(cls, v):
        """Ensure reasonable concurrency limits"""
        if v < 1 or v > 10:
            raise ValueError("LLM_CONCURRENCY must be between 1 and 10")
        return v
    
    @property
    def api_key_list(self) -> List[str]:
        """Parse comma-separated API keys"""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

