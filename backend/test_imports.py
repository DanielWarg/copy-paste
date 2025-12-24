#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.

This is safer than using python -c with long strings.
"""
import sys

print("Step 1: Testing basic imports...", flush=True)
try:
    from uuid import UUID
    print("  ✓ uuid imported", flush=True)
except Exception as e:
    print(f"  ✗ uuid failed: {e}", flush=True)
    sys.exit(1)

print("Step 2: Testing config import...", flush=True)
try:
    from app.core.config import settings
    print(f"  ✓ config imported: ollama_base_url={settings.ollama_base_url}", flush=True)
except Exception as e:
    print(f"  ✗ config failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 3: Testing ollama_client import...", flush=True)
try:
    from app.modules.privacy.ollama_client import ollama_client
    print(f"  ✓ ollama_client imported: base_url={ollama_client.base_url}", flush=True)
except Exception as e:
    print(f"  ✗ ollama_client failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 4: Testing privacy_v2_service import...", flush=True)
try:
    from app.modules.privacy_v2.privacy_v2_service import scrub_v2
    print("  ✓ privacy_v2_service imported", flush=True)
except Exception as e:
    print(f"  ✗ privacy_v2_service failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 5: Testing layer2_verify import...", flush=True)
try:
    from app.modules.privacy_v2.layer2_verify import verify_anonymization
    print("  ✓ layer2_verify imported", flush=True)
except Exception as e:
    print(f"  ✗ layer2_verify failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 6: Testing layer3_semantic_audit import...", flush=True)
try:
    from app.modules.privacy_v2.layer3_semantic_audit import semantic_audit
    print("  ✓ layer3_semantic_audit imported", flush=True)
except Exception as e:
    print(f"  ✗ layer3_semantic_audit failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All imports successful!", flush=True)

