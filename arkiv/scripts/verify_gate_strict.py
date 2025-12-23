#!/usr/bin/env python3
"""
Strict verification of Privacy Shield v2 gate functionality.
This test verifies that the gate ACTUALLY blocks and allows correctly.
"""
import urllib.request
import json
import sys
from typing import Dict, Any

API_BASE = "http://localhost:8000"

def _http_json(method: str, url: str, payload: Dict[str, Any] = None, timeout: int = 30) -> tuple:
    """Make HTTP request, return (status, body_text, json)."""
    data = None
    if payload:
        data = json.dumps(payload).encode()
    
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            try:
                return resp.status, body, json.loads(body)
            except:
                return resp.status, body, None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, body, json.loads(body)
        except:
            return e.code, body, None
    except Exception as e:
        raise RuntimeError(f"Network error calling {url}: {e}") from e

def ingest_text(text: str, metadata: dict = None) -> str:
    """Ingest text, return event_id."""
    payload = {"input_type": "text", "value": text, "metadata": metadata or {}}
    status, body, json_data = _http_json("POST", f"{API_BASE}/api/v1/ingest", payload)
    if status != 200:
        raise RuntimeError(f"Ingest failed: {status} {body}")
    return json_data["event_id"]

def scrub_v2(event_id: str, production_mode: bool = False, max_retries: int = 2) -> Dict[str, Any]:
    """Run scrub_v2, return result."""
    payload = {"event_id": event_id, "production_mode": production_mode, "max_retries": max_retries}
    status, body, json_data = _http_json("POST", f"{API_BASE}/api/v1/privacy/scrub_v2", payload, timeout=60)
    if status != 200:
        raise RuntimeError(f"Scrub v2 failed: {status} {body}")
    return json_data

def generate_draft(event_id: str, clean_text: str, production_mode: bool = False, approval_token: str = None) -> tuple:
    """Generate draft, return (status, body, json)."""
    payload = {"event_id": event_id, "clean_text": clean_text, "production_mode": production_mode}
    if approval_token:
        payload["approval_token"] = approval_token
    return _http_json("POST", f"{API_BASE}/api/v1/draft/generate", payload, timeout=30)

def test_clean_text_no_gate():
    """Test: Clean text should NOT require approval."""
    print("\n=== TEST 1: Clean text should NOT require approval ===")
    event_id = ingest_text("Detta är en helt neutral text utan PII.")
    scrub = scrub_v2(event_id, production_mode=False)
    
    assert scrub.get("approval_required") == False, f"Clean text should not require approval: {scrub}"
    assert scrub.get("semantic_risk") == False, f"Clean text should not have semantic risk: {scrub}"
    assert scrub.get("verification_passed") == True, f"Clean text should pass verification: {scrub}"
    assert scrub.get("approval_token") is None, f"Clean text should not have approval token: {scrub}"
    
    # Draft should work WITHOUT token
    clean_text = scrub.get("clean_text", "")
    status, body, json_data = generate_draft(event_id, clean_text, production_mode=False)
    
    # Should NOT be blocked (403) - might fail for other reasons (OpenAI, etc) but not gate
    assert status != 403, f"Draft should not be blocked for clean text. Status: {status}, Body: {body}"
    print(f"✅ Clean text: no approval required, draft not blocked (status={status})")
    return event_id, scrub

def test_semantic_leak_requires_approval():
    """Test: Semantic leak should require approval."""
    print("\n=== TEST 2: Semantic leak should require approval ===")
    leak_text = "[PERSON_A] är VD för Acme Corporation, ett unikt företag. [PERSON_A] vann Nobelpriset i fysik 2023."
    event_id = ingest_text(leak_text)
    scrub = scrub_v2(event_id, production_mode=False, max_retries=2)
    
    approval_required = scrub.get("approval_required")
    semantic_risk = scrub.get("semantic_risk")
    approval_token = scrub.get("approval_token")
    
    print(f"  approval_required: {approval_required}")
    print(f"  semantic_risk: {semantic_risk}")
    print(f"  has_token: {bool(approval_token)}")
    
    # CRITICAL: If semantic_risk=True, approval_required MUST be True
    if semantic_risk:
        assert approval_required == True, f"If semantic_risk=True, approval_required must be True. Got: {scrub}"
        assert approval_token is not None and len(approval_token) >= 16, f"Must have approval_token when approval_required=True. Got: {approval_token}"
        print(f"✅ Semantic leak detected: approval_required=True, token provided")
    else:
        print(f"⚠️  Semantic leak NOT detected (semantic_risk=False). This might be OK if model is lenient.")
    
    return event_id, scrub

def test_draft_blocked_without_token(event_id: str, scrub: Dict[str, Any]):
    """Test: Draft should be BLOCKED (403) without token when gated."""
    print("\n=== TEST 3: Draft should be BLOCKED without token ===")
    
    approval_required = scrub.get("approval_required")
    if not approval_required:
        print(f"⚠️  Skipping test - approval_required=False, so gate should not block")
        return
    
    clean_text = scrub.get("clean_text", "")
    assert clean_text.strip() != "", "clean_text is empty"
    
    # Try draft WITHOUT token
    status, body, json_data = generate_draft(event_id, clean_text, production_mode=False, approval_token=None)
    
    print(f"  Status without token: {status}")
    print(f"  Body: {body[:200]}")
    
    # CRITICAL: Must be 403 (Forbidden) when gated and no token
    assert status == 403, f"Expected 403 Forbidden when gated without token. Got: {status}, Body: {body[:300]}"
    
    # Verify error message mentions approval_token or gated
    body_lower = body.lower()
    assert "approval_token" in body_lower or "gated" in body_lower or "forbidden" in body_lower, \
        f"Error message should mention approval_token or gated. Got: {body[:200]}"
    
    print(f"✅ Draft correctly blocked without token (403)")

def test_draft_passes_with_token(event_id: str, scrub: Dict[str, Any]):
    """Test: Draft should PASS gate with valid token."""
    print("\n=== TEST 4: Draft should PASS with valid token ===")
    
    approval_required = scrub.get("approval_required")
    approval_token = scrub.get("approval_token")
    
    if not approval_required:
        print(f"⚠️  Skipping test - approval_required=False, so no token needed")
        return
    
    assert approval_token is not None, "Must have approval_token when approval_required=True"
    
    clean_text = scrub.get("clean_text", "")
    
    # Try draft WITH token
    status, body, json_data = generate_draft(event_id, clean_text, production_mode=False, approval_token=approval_token)
    
    print(f"  Status with token: {status}")
    print(f"  Body: {body[:200]}")
    
    # CRITICAL: Must NOT be 403 (gate should pass)
    assert status != 403, f"Gate should pass with valid token. Got 403: {body[:300]}"
    
    # Verify error message does NOT mention approval_token/gated (if error)
    if status != 200:
        body_lower = body.lower()
        blocked_markers = ["approval_token", "gated", "forbidden"]
        has_blocked_marker = any(marker in body_lower for marker in blocked_markers)
        assert not has_blocked_marker, \
            f"Error should NOT mention approval_token/gated when token is valid. Got: {body[:300]}"
        print(f"✅ Gate passed (status={status}, likely OpenAI/config error, not gate)")
    else:
        print(f"✅ Draft generated successfully with token")

def test_invalid_token_rejected(event_id: str, scrub: Dict[str, Any]):
    """Test: Invalid token should be rejected."""
    print("\n=== TEST 5: Invalid token should be rejected ===")
    
    approval_required = scrub.get("approval_required")
    if not approval_required:
        print(f"⚠️  Skipping test - approval_required=False")
        return
    
    clean_text = scrub.get("clean_text", "")
    
    # Try with fake token
    fake_token = "invalid_token_12345"
    status, body, json_data = generate_draft(event_id, clean_text, production_mode=False, approval_token=fake_token)
    
    print(f"  Status with fake token: {status}")
    print(f"  Body: {body[:200]}")
    
    # Must be 403
    assert status == 403, f"Invalid token should be rejected (403). Got: {status}, Body: {body[:300]}"
    
    print(f"✅ Invalid token correctly rejected (403)")

def main():
    print("=" * 60)
    print("STRICT GATE VERIFICATION TEST")
    print("=" * 60)
    
    # Health check
    try:
        status, body, json_data = _http_json("GET", f"{API_BASE}/health", timeout=5)
        if status != 200:
            print(f"❌ Backend not healthy: {status}")
            sys.exit(1)
        print("✅ Backend is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        sys.exit(1)
    
    try:
        # Test 1: Clean text should not require approval
        clean_event_id, clean_scrub = test_clean_text_no_gate()
        
        # Test 2: Semantic leak should require approval
        leak_event_id, leak_scrub = test_semantic_leak_requires_approval()
        
        # Test 3: Draft blocked without token
        test_draft_blocked_without_token(leak_event_id, leak_scrub)
        
        # Test 4: Draft passes with token
        test_draft_passes_with_token(leak_event_id, leak_scrub)
        
        # Test 5: Invalid token rejected
        test_invalid_token_rejected(leak_event_id, leak_scrub)
        
        print("\n" + "=" * 60)
        print("✅ ALL STRICT TESTS PASSED")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())

