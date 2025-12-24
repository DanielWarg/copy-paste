#!/usr/bin/env python3
"""
Test med clean text som inte ska trigga semantic risk
"""
import urllib.request
import json
import sys

API_BASE = "http://localhost:8000"

def test_clean_text_flow():
    """Test med text som inte innehåller identifierbar PII"""
    print("=== Test: Clean Text Flow (No Semantic Risk) ===\n")
    
    # Clean text utan identifierbar PII eller hög specificitet
    clean_text = "Idag hölls ett möte på kommunhuset där flera ämnen diskuterades. Mötet varade i två timmar och deltagarna var nöjda med resultatet."
    
    # Ingest
    payload = {"input_type": "text", "value": clean_text, "metadata": {"test": "clean_flow"}}
    req = urllib.request.Request(f"{API_BASE}/api/v1/ingest", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    event_id = json.loads(resp.read().decode())["event_id"]
    print(f"✅ Ingest: {event_id}")
    
    # Privacy Shield v2
    payload = {"event_id": event_id, "production_mode": False, "max_retries": 2}
    req = urllib.request.Request(f"{API_BASE}/api/v1/privacy/scrub_v2", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=90)
    scrub_result = json.loads(resp.read().decode())
    
    print(f"✅ Privacy Shield v2:")
    print(f"   Verification passed: {scrub_result.get('verification_passed')}")
    print(f"   Semantic risk: {scrub_result.get('semantic_risk')}")
    print(f"   Approval required: {scrub_result.get('approval_required')}")
    print(f"   Is anonymized: {scrub_result.get('is_anonymized')}")
    
    # Draft generation
    clean_text_scrubbed = scrub_result.get("clean_text", "")
    approval_token = scrub_result.get("approval_token")
    approval_required = scrub_result.get("approval_required", False)
    
    payload = {"event_id": event_id, "clean_text": clean_text_scrubbed, "production_mode": False}
    if approval_required and approval_token:
        payload["approval_token"] = approval_token
    
    req = urllib.request.Request(f"{API_BASE}/api/v1/draft/generate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        draft_result = json.loads(resp.read().decode())
        print(f"✅ Draft Generation:")
        draft_text = draft_result.get("text") or draft_result.get("draft") or draft_result.get("content", "")
        citations = draft_result.get("citations", [])
        print(f"   Draft length: {len(draft_text)} chars")
        print(f"   Citations: {len(citations)}")
        print(f"\n   Draft preview:\n   {draft_text[:300]}...")
        return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"⚠️  Draft Generation: {e.code}")
        print(f"   {error_body[:200]}")
        if "is_anonymized" in error_body:
            print("   (Blocked because is_anonymized=False - korrekt beteende)")
        return False

if __name__ == "__main__":
    try:
        success = test_clean_text_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

