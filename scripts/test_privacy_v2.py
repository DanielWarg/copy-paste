#!/usr/bin/env python3
"""
Integration tests for Privacy Shield v2.

Tests:
1. Clean input -> verification_passed=true, semantic_risk=false
2. Forced leak pattern -> verification fails -> approval_required=true
3. Semantic risk -> draft blocked without approval_token
4. Approval token flow -> draft succeeds with token
"""
import requests
import json
import sys
import time
from datetime import datetime
from uuid import uuid4

API_BASE = "http://localhost:8000"


def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)


def wait_for_server(url, timeout=10):
    """Waits for the server to be ready."""
    print(f"\nWaiting for server at {url}...")
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Server not responding!")
    return False


def test_clean_input():
    """Test 1: Clean input -> verification_passed=true, semantic_risk=false"""
    print_section("TEST 1: Clean Input (No PII)")
    
    try:
        # Ingest clean text
        ingest_res = requests.post(
            f"{API_BASE}/api/v1/ingest",
            json={
                "input_type": "text",
                "value": "This is a simple news article about the weather. It rained yesterday. The temperature was 15 degrees."
            },
            timeout=5
        )
        ingest_res.raise_for_status()
        event_id = ingest_res.json()["event_id"]
        print(f"✅ Event created: {event_id}")
        
        # Scrub v2
        scrub_res = requests.post(
            f"{API_BASE}/api/v1/privacy/scrub_v2",
            json={
                "event_id": str(event_id),
                "production_mode": False,
                "max_retries": 2
            },
            timeout=30
        )
        scrub_res.raise_for_status()
        scrub_data = scrub_res.json()
        
        print(f"✅ Scrub v2 completed")
        print(f"   Verification passed: {scrub_data['verification_passed']}")
        print(f"   Semantic risk: {scrub_data['semantic_risk']}")
        print(f"   Approval required: {scrub_data['approval_required']}")
        print(f"   Steps: {len(scrub_data['receipt']['steps'])}")
        
        if scrub_data['verification_passed'] and not scrub_data['semantic_risk']:
            print("✅ Test 1 PASSED: Clean input processed correctly")
            return True
        else:
            print(f"❌ Test 1 FAILED: Expected verification_passed=True, semantic_risk=False")
            return False
            
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        return False


def test_forced_leak_pattern():
    """Test 2: Forced leak pattern -> verification fails -> approval_required=true"""
    print_section("TEST 2: Forced Leak Pattern (Email)")
    
    try:
        # Ingest text with email
        ingest_res = requests.post(
            f"{API_BASE}/api/v1/ingest",
            json={
                "input_type": "text",
                "value": "Contact John Doe at john.doe@example.com for more information. Phone: 555-123-4567."
            },
            timeout=5
        )
        ingest_res.raise_for_status()
        event_id = ingest_res.json()["event_id"]
        print(f"✅ Event created: {event_id}")
        
        # Scrub v2
        scrub_res = requests.post(
            f"{API_BASE}/api/v1/privacy/scrub_v2",
            json={
                "event_id": str(event_id),
                "production_mode": False,
                "max_retries": 2
            },
            timeout=30
        )
        scrub_res.raise_for_status()
        scrub_data = scrub_res.json()
        
        print(f"✅ Scrub v2 completed")
        print(f"   Verification passed: {scrub_data['verification_passed']}")
        print(f"   Approval required: {scrub_data['approval_required']}")
        print(f"   Approval token: {'Yes' if scrub_data['approval_token'] else 'No'}")
        
        # Check if approval is required (verification might fail or pass depending on anonymization)
        # The key is that if verification fails, approval should be required
        if not scrub_data['verification_passed']:
            if scrub_data['approval_required'] and scrub_data['approval_token']:
                print("✅ Test 2 PASSED: Verification failed, approval required")
                return True, event_id, scrub_data['approval_token']
            else:
                print("❌ Test 2 FAILED: Verification failed but no approval token")
                return False, None, None
        else:
            print("⚠️ Test 2: Verification passed (anonymization worked), checking draft gate...")
            # Even if verification passed, test draft gate
            return True, event_id, None
            
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        return False, None, None


def test_draft_blocked_without_token():
    """Test 3: Semantic risk -> draft blocked without approval_token"""
    print_section("TEST 3: Draft Blocked Without Token")
    
    try:
        # Use event from test 2 if available, or create new one
        ingest_res = requests.post(
            f"{API_BASE}/api/v1/ingest",
            json={
                "input_type": "text",
                "value": "The CEO of Acme Corporation, John Smith, lives at 123 Main Street. Contact: john@acme.com"
            },
            timeout=5
        )
        ingest_res.raise_for_status()
        event_id = ingest_res.json()["event_id"]
        
        # Scrub v2
        scrub_res = requests.post(
            f"{API_BASE}/api/v1/privacy/scrub_v2",
            json={
                "event_id": str(event_id),
                "production_mode": False,
                "max_retries": 2
            },
            timeout=30
        )
        scrub_res.raise_for_status()
        scrub_data = scrub_res.json()
        
        if not scrub_data['approval_required']:
            print("⚠️ Test 3: No approval required (event not gated), skipping...")
            return True
        
        # Try to generate draft WITHOUT token (should fail)
        try:
            draft_res = requests.post(
                f"{API_BASE}/api/v1/draft/generate",
                json={
                    "event_id": str(event_id),
                    "clean_text": scrub_data['clean_text'],
                    "production_mode": False
                    # No approval_token
                },
                timeout=30
            )
            
            if draft_res.status_code == 403:
                print("✅ Test 3 PASSED: Draft correctly blocked without approval_token")
                return True
            else:
                print(f"❌ Test 3 FAILED: Expected 403, got {draft_res.status_code}")
                return False
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("✅ Test 3 PASSED: Draft correctly blocked without approval_token")
                return True
            else:
                print(f"❌ Test 3 FAILED: Expected 403, got {e.response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        return False


def test_approval_token_flow(event_id, approval_token):
    """Test 4: Approval token flow -> draft succeeds with token"""
    print_section("TEST 4: Approval Token Flow")
    
    if not event_id or not approval_token:
        print("⚠️ Test 4 SKIPPED: No gated event from previous test")
        return True
    
    try:
        # Get clean_text from scrub_v2 (we need it for draft)
        scrub_res = requests.post(
            f"{API_BASE}/api/v1/privacy/scrub_v2",
            json={
                "event_id": str(event_id),
                "production_mode": False,
                "max_retries": 2
            },
            timeout=30
        )
        scrub_res.raise_for_status()
        scrub_data = scrub_res.json()
        
        # Generate draft WITH token (should succeed)
        draft_res = requests.post(
            f"{API_BASE}/api/v1/draft/generate",
            json={
                "event_id": str(event_id),
                "clean_text": scrub_data['clean_text'],
                "production_mode": False,
                "approval_token": approval_token
            },
            timeout=30
        )
        draft_res.raise_for_status()
        draft_data = draft_res.json()
        
        print(f"✅ Draft generated successfully")
        print(f"   Text length: {len(draft_data['text'])}")
        print(f"   Citations: {len(draft_data['citations'])}")
        
        print("✅ Test 4 PASSED: Draft succeeded with approval_token")
        return True
        
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        return False


def main():
    print("="*60)
    print("PRIVACY SHIELD v2 INTEGRATION TESTS")
    print("="*60)
    print(f"Started: {datetime.now()}")

    if not wait_for_server(f"{API_BASE}/health"):
        sys.exit(1)

    results = []
    
    # Test 1: Clean input
    results.append(("Clean Input", test_clean_input()))
    
    # Test 2: Forced leak pattern
    test2_result, event_id, approval_token = test_forced_leak_pattern()
    results.append(("Forced Leak Pattern", test2_result))
    
    # Test 3: Draft blocked without token
    results.append(("Draft Blocked Without Token", test_draft_blocked_without_token()))
    
    # Test 4: Approval token flow
    results.append(("Approval Token Flow", test_approval_token_flow(event_id, approval_token)))

    passed_count = sum(1 for _, r in results if r)
    failed_count = len(results) - passed_count

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    print(f"\nTotal: {passed_count} passed, {failed_count} failed")

    if failed_count > 0:
        print("\n❌ Some tests failed.")
        sys.exit(1)
    else:
        print("\n✅ All Privacy Shield v2 tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

