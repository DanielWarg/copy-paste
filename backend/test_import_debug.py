#!/usr/bin/env python3
"""Debug script to find blocking import."""
import sys
import traceback

print("Step 1: Starting...", flush=True)

try:
    print("Step 2: Importing sys...", flush=True)
    import sys
    print("Step 3: Importing uuid...", flush=True)
    from uuid import UUID
    print("Step 4: Importing fastapi...", flush=True)
    from fastapi import HTTPException
    print("Step 5: Importing app.core.config...", flush=True)
    from app.core.config import settings
    print(f"Step 6: Settings loaded: ollama_base_url={settings.ollama_base_url}", flush=True)
    print("Step 7: Importing httpx...", flush=True)
    import httpx
    print("Step 8: Creating AsyncClient...", flush=True)
    client = httpx.AsyncClient(timeout=10.0)
    print("Step 9: AsyncClient created", flush=True)
    print("Step 10: Importing ollama_client...", flush=True)
    from app.modules.privacy.ollama_client import ollama_client
    print("Step 11: ollama_client imported", flush=True)
    print("Step 12: Importing privacy_v2_service...", flush=True)
    from app.modules.privacy_v2.privacy_v2_service import scrub_v2
    print("✅ All imports OK", flush=True)
except Exception as e:
    print(f"❌ ERROR at step: {e}", flush=True)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

