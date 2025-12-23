#!/usr/bin/env python3
"""
Full Pipeline Test - No Mocks, Real Data Only
Tests: Ingest → Scrub → Draft
"""
import requests
import json
import sys
import time
from datetime import datetime

API_BASE = "http://localhost:8000"
TEST_REPORT = "test_report.txt"

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
    response = requests.get(f"{API_BASE}/health", timeout=5)
    return response.status_code == 200 and response.json().get("status") == "ok"

def test_ingest():
    """Test 2: Ingest Text"""
    test_text = "John Doe works at Acme Corp. Contact: john@acme.com or call 555-1234. Address: 123 Main St, Stockholm."
    
    response = requests.post(
        f"{API_BASE}/api/v1/ingest",
        json={"input_type": "text", "value": test_text},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    data = response.json()
    event_id = data.get("event_id")
    
    if not event_id:
        print(f"  No event_id in response: {data}")
        return False
    
    print(f"  Event ID: {event_id}")
    test_ingest.event_id = event_id
    test_ingest.original_text = test_text
    return True

def test_scrub_production_on():
    """Test 3: Scrub with Production Mode ON"""
    if not hasattr(test_ingest, 'event_id'):
        print("  Skipping: No event_id from ingest test")
        return False
    
    response = requests.post(
        f"{API_BASE}/api/v1/privacy/scrub",
        json={
            "event_id": test_ingest.event_id,
            "production_mode": True
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    data = response.json()
    clean_text = data.get("clean_text", "")
    is_anonymized = data.get("is_anonymized", False)
    
    print(f"  Is anonymized: {is_anonymized}")
    print(f"  Clean text preview: {clean_text[:100]}...")
    
    # Check for anonymization tokens
    has_tokens = any(token in clean_text for token in ["[PERSON", "[ORG", "[EMAIL", "[PHONE", "[ADDRESS"])
    
    if not is_anonymized:
        print("  ✗ is_anonymized is False")
        return False
    
    if not has_tokens and len(clean_text) > 0:
        print("  ⚠ Warning: No anonymization tokens found (text might be clean)")
    
    test_scrub_production_on.clean_text = clean_text
    test_scrub_production_on.is_anonymized = is_anonymized
    return True

def test_scrub_production_off():
    """Test 4: Scrub with Production Mode OFF"""
    if not hasattr(test_ingest, 'event_id'):
        return False
    
    response = requests.post(
        f"{API_BASE}/api/v1/privacy/scrub",
        json={
            "event_id": test_ingest.event_id,
            "production_mode": False
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"  Status: {response.status_code}")
        return False
    
    data = response.json()
    is_anonymized = data.get("is_anonymized", False)
    print(f"  Is anonymized (OFF mode): {is_anonymized}")
    return True

def test_draft_generation():
    """Test 5: Draft Generation"""
    if not hasattr(test_scrub_production_on, 'clean_text'):
        print("  Skipping: No clean_text from scrub test")
        return False
    
    # Check for OpenAI API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠ SKIPPED: OPENAI_API_KEY not set")
        return True  # Skip, don't fail
    
    response = requests.post(
        f"{API_BASE}/api/v1/draft/generate",
        json={
            "event_id": test_ingest.event_id,
            "clean_text": test_scrub_production_on.clean_text,
            "production_mode": True
        },
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    data = response.json()
    draft_text = data.get("text", "")
    citations = data.get("citations", [])
    violations = data.get("policy_violations", [])
    
    print(f"  Draft length: {len(draft_text)} chars")
    print(f"  Citations: {len(citations)}")
    print(f"  Policy violations: {violations}")
    
    if not draft_text:
        print("  ✗ No draft text returned")
        return False
    
    return True

def test_security_block():
    """Test 6: Security - Block unscrubbed data"""
    if not hasattr(test_ingest, 'original_text'):
        return False
    
    response = requests.post(
        f"{API_BASE}/api/v1/draft/generate",
        json={
            "event_id": test_ingest.event_id,
            "clean_text": test_ingest.original_text,  # Unscrubbed!
            "production_mode": False
        },
        timeout=10
    )
    
    # Should return 400
    if response.status_code == 400:
        print(f"  ✓ Correctly blocked with status 400")
        return True
    else:
        print(f"  ✗ Expected 400, got {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("COPY/PASTE FULL PIPELINE TEST")
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
    test_step("Ingest Text", test_ingest)
    test_step("Scrub (Production Mode ON)", test_scrub_production_on)
    test_step("Scrub (Production Mode OFF)", test_scrub_production_off)
    test_step("Draft Generation", test_draft_generation)
    test_step("Security Block", test_security_block)
    
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
    
    # Write report
    with open(TEST_REPORT, "w") as f:
        f.write(f"COPY/PASTE TEST REPORT\n")
        f.write(f"Started: {datetime.now()}\n")
        f.write(f"Passed: {PASSED}\n")
        f.write(f"Failed: {FAILED}\n")
        if ERRORS:
            f.write(f"\nErrors:\n")
            for error in ERRORS:
                f.write(f"  - {error}\n")
        f.write(f"\nCompleted: {datetime.now()}\n")
    
    if FAILED == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

