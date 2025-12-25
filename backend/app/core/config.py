"""Core configuration using Pydantic Settings."""
from pathlib import Path
from typing import List, Optional, Union, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
import os
import sys


def read_secret_file(secret_name: str, default_env_var: Optional[str] = None, required: bool = True) -> Optional[str]:
    """
    Read secret from Docker secret file or environment variable.
    
    In prod_brutal profile: secrets MUST come from /run/secrets/
    In dev/test: fallback to environment variables
    
    Args:
        secret_name: Name of secret file (e.g., 'fernet_key')
        default_env_var: Environment variable name as fallback (e.g., 'FERNET_KEY')
        required: If True, fail in prod_brutal if secret is missing. If False, return None.
        
    Returns:
        Secret value or None if not found (and not required)
        
    Raises:
        SystemExit: If secret is required in prod_brutal but missing
    """
    profile = os.getenv("PROFILE", "").lower()
    environment = os.getenv("ENVIRONMENT", "").lower()
    
    # In prod_brutal, secrets MUST come from /run/secrets/
    if profile == "prod_brutal" or (environment == "production" and profile == "prod_brutal"):
        secret_path = Path(f"/run/secrets/{secret_name}")
        if secret_path.exists():
            try:
                return secret_path.read_text().strip()
            except Exception as e:
                error_type = type(e).__name__
                print(f"ERROR: Failed to read secret {secret_name}: {error_type}", file=sys.stderr)
                sys.exit(1)
        else:
            # If required, fail. Otherwise return None (for optional secrets like openai_api_key in prod_brutal)
            if required:
                print(f"ERROR: Required secret {secret_name} not found in /run/secrets/ (prod_brutal profile)", file=sys.stderr)
                sys.exit(1)
            return None
    
    # In dev/test, fallback to environment variable
    if default_env_var:
        return os.getenv(default_env_var)
    
    return None


class Settings(BaseSettings):
    """Application settings with fail-fast validation."""
    
    # App metadata
    app_name: str = Field(default="Copy/Paste Backend", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    
    # Environment
    environment: str = Field(default="development", description="Environment (development|production)")
    profile: str = Field(default="dev", description="Profile (dev|prod_brutal)")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./data/app.db",
        description="Database URL"
    )
    db_health_timeout_seconds: float = Field(
        default=2.0,
        description="Database health check timeout in seconds"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
        description="CORS allowed origins"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json|text)")
    log_sample_rate: float = Field(default=1.0, description="Log sampling rate (0.0-1.0)")
    
    # Meta endpoint
    enable_meta: bool = Field(default=False, description="Enable /meta endpoint")
    
    # Privacy Shield settings
    privacy_max_chars: int = Field(default=50000, description="Maximum characters for privacy masking")
    privacy_timeout_seconds: int = Field(default=10, description="Privacy Shield timeout")
    allow_external: bool = Field(default=False, description="Allow external LLM calls")
    llamacpp_base_url: Optional[str] = Field(default=None, description="LLaMA.cpp base URL (optional)")
    
    # Source Safety Mode (forced to True in production)
    source_safety_mode: bool = Field(default=True, description="Source safety mode (forced True in production)")
    
    # Retention Policy
    retention_days_default: int = Field(default=30, description="Default retention days for projects")
    retention_days_sensitive: int = Field(default=7, description="Retention days for sensitive projects")
    temp_file_ttl_hours: int = Field(default=24, description="TTL for temporary files (hours)")
    
    # Secrets (read from /run/secrets/ in prod_brutal, env vars in dev)
    fernet_key: Optional[str] = Field(default=None, description="Fernet encryption key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    project_files_key: Optional[str] = Field(default=None, description="Project files encryption key (base64-encoded Fernet key)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        """Initialize settings with secret file support."""
        # Read secrets before calling super().__init__
        profile = os.getenv("PROFILE", kwargs.get("profile", "dev")).lower()
        environment = os.getenv("ENVIRONMENT", kwargs.get("environment", "development")).lower()
        
        # Read secrets from files or env
        # fernet_key is REQUIRED in prod_brutal
        fernet_secret = read_secret_file("fernet_key", "FERNET_KEY", required=True)
        if fernet_secret:
            kwargs["fernet_key"] = fernet_secret
        
        # openai_api_key is OPTIONAL in prod_brutal (should NOT exist, validated in _validate_prod_brutal)
        openai_secret = read_secret_file("openai_api_key", "OPENAI_API_KEY", required=False)
        if openai_secret:
            kwargs["openai_api_key"] = openai_secret
        
        super().__init__(**kwargs)
        
        # Source Safety Mode: Force to True in production (fail-closed)
        if not self.debug and not self.source_safety_mode:
            error_msg = "SOURCE_SAFETY_MODE cannot be False in production (DEBUG=false). Source protection is mandatory for newsroom operations."
            print(f"ERROR: {error_msg}", file=sys.stderr)
            raise ValueError(error_msg)
        
        # Force source_safety_mode to True in production
        if not self.debug:
            self.source_safety_mode = True
        
        # Validate prod_brutal profile requirements
        if profile == "prod_brutal" or (environment == "production" and profile == "prod_brutal"):
            self._validate_prod_brutal()
    
    def _validate_prod_brutal(self) -> None:
        """Validate prod_brutal profile requirements."""
        # Check that cloud API keys are NOT set (fail-closed)
        if self.openai_api_key:
            print("ERROR: OPENAI_API_KEY found in prod_brutal profile - external egress is blocked", file=sys.stderr)
            sys.exit(1)
        
        # Check that required secrets exist
        if not self.fernet_key:
            print("ERROR: FERNET_KEY required in prod_brutal profile", file=sys.stderr)
            sys.exit(1)


# Global settings instance
settings = Settings()
