#!/usr/bin/env python3
"""Test CORS_ORIGINS parsing from environment variable."""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# Test with comma-separated string (as it appears in .env)
os.environ["CORS_ORIGINS"] = "http://localhost:5173,http://localhost:3000"

class TestSettings(BaseSettings):
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], alias="CORS_ORIGINS"
    )
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


settings = TestSettings()
print(f"✅ CORS origins parsed: {settings.cors_origins}")
print(f"✅ Type: {type(settings.cors_origins)}")
print(f"✅ Contains 5173: {'http://localhost:5173' in settings.cors_origins}")
print(f"✅ Contains 3000: {'http://localhost:3000' in settings.cors_origins}")

if "http://localhost:5173" not in settings.cors_origins:
    print("❌ ERROR: http://localhost:5173 not found in CORS origins!")
    sys.exit(1)

print("\n✅ CORS parsing test PASSED")

