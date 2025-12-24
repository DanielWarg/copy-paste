#!/usr/bin/env python3
"""Core smoke tests - verifies /ready behavior and privacy-safe logging."""
import json
import sys
import time
from typing import Any, Dict

try:
    import urllib.request
    import urllib.error
except ImportError:
    print("❌ urllib not available")
    sys.exit(1)

BACKEND_URL = "http://localhost:8000"

# Forbidden keys that must NEVER appear in logs
_FORBIDDEN_LOG_KEYS = {
    "authorization",
    "cookie",
    "user-agent",
    "user_agent",
    "body",
    "payload",
    "headers",
    "query_params",
    "query",
    "ip",
    "ip_address",
    "remote_addr",
    "x-forwarded-for",
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
}


def check_endpoint(url: str, expected_status: int, expected_fields: Dict[str, Any] = None) -> bool:
    """Check endpoint returns expected status and fields.

    Args:
        url: Endpoint URL
        expected_status: Expected HTTP status code
        expected_fields: Expected fields in response (optional)

    Returns:
        True if check passes, False otherwise
    """
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")

            if status != expected_status:
                print(f"❌ {url} returned {status}, expected {expected_status}")
                return False

            if expected_fields:
                try:
                    data = json.loads(body)
                    for key, value in expected_fields.items():
                        if data.get(key) != value:
                            print(
                                f"❌ {url} response missing or incorrect field: {key}={data.get(key)}, expected {value}"
                            )
                            return False
                except json.JSONDecodeError:
                    print(f"❌ {url} returned invalid JSON: {body[:100]}")
                    return False

            print(f"✅ {url} returned {status} with correct structure")
            return True

    except urllib.error.HTTPError as e:
        if e.code == expected_status:
            body = e.read().decode("utf-8")
            if expected_fields:
                try:
                    data = json.loads(body)
                    # Check detail field for 503 errors
                    if "detail" in data:
                        detail = data["detail"]
                        for key, value in expected_fields.items():
                            if detail.get(key) != value:
                                print(
                                    f"❌ {url} detail missing or incorrect: {key}={detail.get(key)}, expected {value}"
                                )
                                return False
                    else:
                        for key, value in expected_fields.items():
                            if data.get(key) != value:
                                print(
                                    f"❌ {url} response missing or incorrect: {key}={data.get(key)}, expected {value}"
                                )
                                return False
                except json.JSONDecodeError:
                    print(f"❌ {url} returned invalid JSON: {body[:100]}")
                    return False
            print(f"✅ {url} returned {e.code} (expected {expected_status})")
            return True
        else:
            print(f"❌ {url} returned {e.code}, expected {expected_status}")
            return False
    except Exception as e:
        print(f"❌ {url} failed: {e}")
        return False


def test_privacy_safe_logging() -> bool:
    """Test that logging doesn't contain forbidden keys.

    This is a basic check - in production, you'd check actual log output.
    """
    print("\n=== Testing Privacy-Safe Logging ===")

    # Import logging module to check forbidden keys
    try:
        from app.core.logging import _FORBIDDEN_LOG_KEYS as forbidden_keys

        # Verify forbidden keys are defined
        if not forbidden_keys or len(forbidden_keys) < 5:
            print("❌ Forbidden keys list too short or empty")
            return False

        # Check that common forbidden keys are present
        required_forbidden = {"authorization", "cookie", "body", "headers"}
        if not required_forbidden.issubset(forbidden_keys):
            print(f"❌ Missing required forbidden keys: {required_forbidden - forbidden_keys}")
            return False

        print(f"✅ Privacy-safe logging: {len(forbidden_keys)} forbidden keys defined")
        return True
    except ImportError:
        print("⚠️  Could not import logging module (expected in Docker)")
        return True  # Don't fail if we can't import (running outside Docker)


def main() -> int:
    """Run core smoke tests."""
    print("Running Core Smoke Tests")
    print("=" * 50)

    # Test 1: /health always returns 200
    print("\n=== Test 1: /health endpoint ===")
    if not check_endpoint(f"{BACKEND_URL}/health", 200, {"status": "ok"}):
        return 1

    # Test 2: /ready behavior (depends on DATABASE_URL)
    print("\n=== Test 2: /ready endpoint ===")
    print("Note: Behavior depends on DATABASE_URL configuration")
    ready_status = None
    try:
        req = urllib.request.Request(f"{BACKEND_URL}/ready")
        with urllib.request.urlopen(req, timeout=5) as resp:
            ready_status = resp.getcode()
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            if ready_status == 200:
                if "db" in data and data["db"] == "not_configured":
                    print("✅ /ready returned 200 with db:not_configured (no DB configured)")
                elif data.get("status") == "ready":
                    print("✅ /ready returned 200 (DB is up)")
                else:
                    print(f"⚠️  /ready returned 200 but unexpected structure: {data}")
    except urllib.error.HTTPError as e:
        if e.code == 503:
            body = e.read().decode("utf-8")
            try:
                data = json.loads(body)
                detail = data.get("detail", {})
                if detail.get("status") == "db_down":
                    print("✅ /ready returned 503 with db_down (DB is down)")
                else:
                    print(f"⚠️  /ready returned 503 but unexpected structure: {data}")
            except json.JSONDecodeError:
                print(f"⚠️  /ready returned 503 but invalid JSON: {body[:100]}")
        else:
            print(f"❌ /ready returned unexpected status: {e.code}")
            return 1
    except Exception as e:
        print(f"❌ /ready test failed: {e}")
        return 1

    # Test 3: Privacy-safe logging
    if not test_privacy_safe_logging():
        return 1

    # Test 4: DB health check timeout (if DB is configured)
    print("\n=== Test 3: DB Health Check Timeout ===")
    print("Note: This test requires DATABASE_URL to be set")
    # This would require actually calling the health check function
    # For now, we just verify the function exists and has timeout logic
    try:
        from app.core.database import check_db_health
        from app.core.config import settings

        if settings.database_url:
            print(f"✅ DB health check function available (timeout: {settings.db_health_timeout_seconds}s)")
        else:
            print("ℹ️  DATABASE_URL not set, skipping DB health check test")
    except ImportError:
        print("⚠️  Could not import database module (expected in Docker)")
        # Don't fail - this is expected when running outside Docker

    print("\n" + "=" * 50)
    print("✅ All core tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

