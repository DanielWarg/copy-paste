"""Application configuration with Pydantic Settings.

Fail-fast validation on import. Reads .env from repo root.
"""
from pathlib import Path
from typing import Any, List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with fail-fast validation."""

    # App
    app_name: str = "Copy/Paste Core"
    app_version: str = "2.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (optional)
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    db_health_timeout_seconds: float = Field(default=2.0, alias="DB_HEALTH_TIMEOUT_SECONDS")

    # Security
    cors_origins: Union[str, List[str], None] = Field(
        default=None,
        alias="CORS_ORIGINS",
    )
    api_key_header: Optional[str] = Field(default=None, alias="API_KEY_HEADER")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS_ORIGINS from comma-separated string or list.
        
        Supports both formats:
        - Comma-separated string: "http://localhost:5173,http://localhost:3000"
        - List: ["http://localhost:5173", "http://localhost:3000"]
        """
        if v is None:
            return ["http://localhost:5173", "http://localhost:3000"]
        if isinstance(v, list):
            return [origin.strip() for origin in v if origin.strip()]
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return ["http://localhost:5173", "http://localhost:3000"]
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    log_sample_rate: float = Field(default=1.0, alias="LOG_SAMPLE_RATE")

    # Features
    enable_meta: bool = Field(default=False, alias="ENABLE_META")
    
    # Source Safety Mode (journalistic source protection)
    # HARD MODE: In production (DEBUG=false), SOURCE_SAFETY_MODE is ALWAYS forced to True
    source_safety_mode: bool = Field(default=True, alias="SOURCE_SAFETY_MODE")
    
    # Retention policy (days)
    retention_days_default: int = Field(default=30, alias="RETENTION_DAYS_DEFAULT")
    retention_days_sensitive: int = Field(default=7, alias="RETENTION_DAYS_SENSITIVE")
    temp_file_ttl_hours: int = Field(default=24, alias="TEMP_FILE_TTL_HOURS")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent.parent / ".env",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, __context: Any) -> None:
        """Validate settings after initialization."""
        # Ensure cors_origins is a list
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:5173", "http://localhost:3000"]
        elif isinstance(self.cors_origins, str):
            if not self.cors_origins.strip():
                self.cors_origins = ["http://localhost:5173", "http://localhost:3000"]
            else:
                self.cors_origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        elif isinstance(self.cors_origins, list):
            self.cors_origins = [origin.strip() for origin in self.cors_origins if origin.strip()]
        else:
            self.cors_origins = ["http://localhost:5173", "http://localhost:3000"]
        
        # CORS sanity guard: fail-fast if wide-open CORS in production
        if not self.debug and "*" in self.cors_origins:
            raise ValueError(
                "CORS origins cannot contain '*' in production (debug=False). "
                "This is a security risk. Set specific origins or enable debug mode."
            )
        
        # HARD MODE: Force SOURCE_SAFETY_MODE=True in production
        # This cannot be disabled in production - fail-fast if someone tries
        if not self.debug and not self.source_safety_mode:
            raise ValueError(
                "SOURCE_SAFETY_MODE cannot be False in production (DEBUG=false). "
                "Source protection is mandatory for newsroom operations. "
                "Set DEBUG=true for development if you need to disable source safety mode."
            )
        
        # If in production and source_safety_mode was explicitly set to False, force it to True
        if not self.debug:
            self.source_safety_mode = True


# Fail-fast: Settings validates on import
settings = Settings()
