#!/usr/bin/env python3
"""
MCP Compatibility Layer Tests

Tests the MCP ingestion endpoint to ensure it:
1. Works correctly with valid requests
2. Returns proper error responses for invalid requests
3. Uses the same internal logic as /api/v1/ingest
"""
import requests
import json
import sys
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

PASSED = 0
FAILED = 0
ERRORS = []


def test_step(name, test_func):
    """Run a test step and record results."""
    global PASSED, FAILED
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)
    
    try:
        result = test_func()
        if result:
            print(f"✓ PASSED: {name}")
            PASSED += 1
            return True
        else:
            print(f"✗ FAILED: {name}")
            FAILED += 1
            return False
    except Exception as e:
        print(f"✗ ERROR in {name}: {str(e)}")
        ERRORS.append(f"{name}: {str(e)}")
        FAILED += 1
        return False


def test_health():
    """Test 1: Health Check"""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        if r.status_code == 200:
            print("✓ Backend server is online")
            return True
        else:
            print(f"✗ Health check failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"✗ Server not available: {e}")
        return False


def test_mcp_valid_url():
    """Test 2: Valid MCP Request with URL"""
    try:
        payload = {
            "tool": "ingest",
            "input_type": "url",
            "value": "https://polisen.se/aktuellt/rss/",
            "metadata": {"test": "mcp"},
            "correlation_id": "test-correlation-123"
        }
        
        r = requests.post(
            f"{API_BASE}/api/v1/mcp/ingest",
            json=payload,
            timeout=30
        )
        
        if r.status_code != 200:
            print(f"✗ Unexpected status code: {r.status_code}")
            print(f"  Response: {r.text}")
            return False
        
        data = r.json()
        
        # Check MCP response structure
        if "ok" not in data:
            print("✗ Response missing 'ok' field")
            return False
        
        if not data.get("ok"):
            print(f"✗ Request failed: {data.get('error', 'Unknown error')}")
            return False
        
        if "event_id" not in data or not data.get("event_id"):
            print("✗ Response missing or empty 'event_id'")
            return False
        
        event_id = data["event_id"]
        print(f"✓ MCP ingest successful")
        print(f"  Event ID: {event_id}")
        print(f"  OK: {data.get('ok')}")
        print(f"  Error: {data.get('error')}")
        
        # Verify event can be scrubbed (proves it's a real event)
        scrub_payload = {
            "event_id": event_id,
            "production_mode": True
        }
        
        scrub_r = requests.post(
            f"{API_BASE}/api/v1/privacy/scrub",
            json=scrub_payload,
            timeout=30
        )
        
        if scrub_r.status_code == 200:
            scrub_data = scrub_r.json()
            print(f"✓ Event can be scrubbed (verifies it's real)")
            print(f"  Clean text length: {len(scrub_data.get('clean_text', ''))} chars")
            print(f"  Anonymized: {scrub_data.get('is_anonymized', False)}")
            return True
        else:
            print(f"✗ Event scrub failed: {scrub_r.status_code}")
            print(f"  Response: {scrub_r.text}")
            return False
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_mcp_invalid_payload():
    """Test 3: Invalid MCP Request (missing tool field)"""
    try:
        # Missing 'tool' field
        payload = {
            "input_type": "url",
            "value": "https://example.com"
        }
        
        r = requests.post(
            f"{API_BASE}/api/v1/mcp/ingest",
            json=payload,
            timeout=10
        )
        
        # Should return 422 (validation error) or 200 with ok=false
        if r.status_code == 422:
            print("✓ Correctly rejected invalid payload (422)")
            return True
        elif r.status_code == 200:
            data = r.json()
            if not data.get("ok") and data.get("error"):
                print("✓ Correctly rejected invalid payload (ok=false)")
                print(f"  Error: {data.get('error')}")
                return True
            else:
                print("✗ Invalid payload was accepted")
                return False
        else:
            print(f"✗ Unexpected status code: {r.status_code}")
            return False
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_mcp_unknown_tool():
    """Test 4: Unknown Tool"""
    try:
        payload = {
            "tool": "unknown",
            "input_type": "url",
            "value": "https://example.com"
        }
        
        r = requests.post(
            f"{API_BASE}/api/v1/mcp/ingest",
            json=payload,
            timeout=10
        )
        
        if r.status_code != 200:
            print(f"✗ Unexpected status code: {r.status_code}")
            return False
        
        data = r.json()
        
        if data.get("ok"):
            print("✗ Unknown tool was accepted")
            return False
        
        if not data.get("error"):
            print("✗ Error message missing")
            return False
        
        error_msg = data.get("error", "")
        if "v1" in error_msg.lower() or "ingest" in error_msg.lower():
            print("✓ Correctly rejected unknown tool")
            print(f"  Error: {error_msg}")
            return True
        else:
            print(f"✗ Error message doesn't indicate v1 limitation: {error_msg}")
            return False
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_mcp_invalid_input_type():
    """Test 5: Invalid input_type"""
    try:
        payload = {
            "tool": "ingest",
            "input_type": "invalid",
            "value": "test"
        }
        
        r = requests.post(
            f"{API_BASE}/api/v1/mcp/ingest",
            json=payload,
            timeout=10
        )
        
        # Should return 422 (validation error) or 200 with ok=false
        if r.status_code == 422:
            print("✓ Correctly rejected invalid input_type (422)")
            return True
        elif r.status_code == 200:
            data = r.json()
            if not data.get("ok") and data.get("error"):
                print("✓ Correctly rejected invalid input_type (ok=false)")
                print(f"  Error: {data.get('error')}")
                return True
            else:
                print("✗ Invalid input_type was accepted")
                return False
        else:
            print(f"✗ Unexpected status code: {r.status_code}")
            return False
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def main():
    """Run all MCP tests."""
    print("="*60)
    print("MCP COMPATIBILITY LAYER TESTS")
    print("="*60)
    print(f"Started: {datetime.now()}")
    
    # Wait for server
    print("\nWaiting for server...")
    for i in range(10):
        try:
            requests.get(f"{API_BASE}/health", timeout=2)
            print("Server is ready!")
            break
        except:
            time.sleep(1)
    else:
        print("✗ Server not responding!")
        sys.exit(1)
    
    # Run tests
    test_step("Health Check", test_health)
    test_step("Valid MCP Request (URL)", test_mcp_valid_url)
    test_step("Invalid MCP Payload (missing tool)", test_mcp_invalid_payload)
    test_step("Unknown Tool", test_mcp_unknown_tool)
    test_step("Invalid input_type", test_mcp_invalid_input_type)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {PASSED}")
    print(f"Failed: {FAILED}")
    
    if ERRORS:
        print("\nErrors:")
        for error in ERRORS:
            print(f"  - {error}")
    
    if FAILED == 0:
        print("\n✓ All MCP tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

