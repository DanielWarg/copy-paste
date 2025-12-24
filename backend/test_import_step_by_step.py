#!/usr/bin/env python3
"""
Step-by-step import test to find what blocks.
Run this and see where it stops.
"""
import sys
import time

def test_import(name, import_func):
    """Test an import with timing."""
    start = time.time()
    try:
        print(f"Testing: {name}...", end=" ", flush=True)
        import_func()
        elapsed = time.time() - start
        print(f"OK ({elapsed:.3f}s)", flush=True)
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"FAILED ({elapsed:.3f}s): {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

print("=" * 60)
print("STEP-BY-STEP IMPORT TEST")
print("=" * 60)
print()

# Step 1: Basic Python
if not test_import("uuid", lambda: __import__('uuid')):
    sys.exit(1)

# Step 2: FastAPI
if not test_import("fastapi", lambda: __import__('fastapi')):
    sys.exit(1)

# Step 3: httpx
if not test_import("httpx", lambda: __import__('httpx')):
    sys.exit(1)

# Step 4: pydantic_settings
if not test_import("pydantic_settings", lambda: __import__('pydantic_settings')):
    sys.exit(1)

# Step 5: app.core (just the package)
if not test_import("app.core", lambda: __import__('app.core')):
    sys.exit(1)

# Step 6: app.core.config (THIS IS WHERE IT LIKELY BLOCKS)
print("Testing: app.core.config (may block here)...", end=" ", flush=True)
start = time.time()
try:
    from app.core.config import settings
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)", flush=True)
except Exception as e:
    elapsed = time.time() - start
    print(f"FAILED ({elapsed:.3f}s): {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: app.core.logging
if not test_import("app.core.logging", lambda: __import__('app.core.logging')):
    sys.exit(1)

# Step 8: app.modules.privacy.ollama_client
print("Testing: app.modules.privacy.ollama_client (may block here)...", end=" ", flush=True)
start = time.time()
try:
    from app.modules.privacy.ollama_client import ollama_client
    elapsed = time.time() - start
    print(f"OK ({elapsed:.3f}s)", flush=True)
except Exception as e:
    elapsed = time.time() - start
    print(f"FAILED ({elapsed:.3f}s): {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ ALL IMPORTS SUCCESSFUL")
print("=" * 60)

