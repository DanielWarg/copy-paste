#!/usr/bin/env python3
"""Test that config reads from .env"""
import sys
sys.path.insert(0, 'backend')
from app.core.config import settings

print(f"OpenAI key loaded: {bool(settings.openai_api_key)}")
if settings.openai_api_key:
    print(f"Key prefix: {settings.openai_api_key[:10]}...")
    print(f"Key length: {len(settings.openai_api_key)}")
else:
    print("⚠️  OpenAI key not loaded from .env")

