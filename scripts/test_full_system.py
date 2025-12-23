#!/usr/bin/env python3
"""
Extended System Test - Tests entire Copy/Paste system including Console UI features.

Tests:
1. Backend endpoints (ingest, scrub, draft)
2. Scout endpoints (events, feeds, notifications)
3. Feed administration (CRUD)
4. Auto-notifications
5. Full pipeline from RSS → Draft
6. Config management
"""
import requests
import json
import sys
import time
from datetime import datetime
from uuid import uuid4

BACKEND_URL = "http://localhost:8000"
SCOUT_URL = "http://localhost:8001"

PASSED = 0
FAILED = 0
ERRORS = []


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_test(name, passed, error=None):
    global PASSED, FAILED
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"  {status}: {name}")
    if not passed and error:
        print(f"    Error: {error}")
        ERRORS.append(f"{name}: {error}")
    if passed:
        PASSED += 1
    else:
        FAILED += 1


def wait_for_services(timeout=30):
    """Wait for backend and scout services to be ready."""
    print_section("Waiting for Services")
    
    for i in range(timeout):
        try:
            r1 = requests.get(f"{BACKEND_URL}/health", timeout=2)
            r2 = requests.get(f"{SCOUT_URL}/health", timeout=2)
            if r1.status_code == 200 and r2.status_code == 200:
                print("  ✅ Both services are online")
                return True
        except:
            pass
        time.sleep(1)
    
    print("  ❌ Services not responding")
    return False


# ============================================================================
# BACKEND TESTS
# ============================================================================

def test_backend_ingest():
    """Test backend ingest endpoint."""
    print_section("Backend: Ingest")
    
    try:
        payload = {
            "input_type": "text",
            "value": "Test artikel om AI och journalistik. Detta är en test.",
            "metadata": {"test": True}
        }
        r = requests.post(f"{BACKEND_URL}/api/v1/ingest", json=payload, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if "event_id" in data:
                print_test("Ingest text", True)
                return data["event_id"]
            else:
                print_test("Ingest text", False, "No event_id in response")
                return None
        else:
            print_test("Ingest text", False, f"Status {r.status_code}: {r.text}")
            return None
    except Exception as e:
        print_test("Ingest text", False, str(e))
        return None


def test_backend_scrub(event_id, production_mode=True):
    """Test backend scrub endpoint."""
    print_section("Backend: Scrub")
    
    if not event_id:
        print_test("Scrub (skipped)", False, "No event_id from ingest")
        return None
    
    try:
        payload = {
            "event_id": event_id,
            "production_mode": production_mode
        }
        r = requests.post(f"{BACKEND_URL}/api/v1/privacy/scrub", json=payload, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            if "clean_text" in data and "is_anonymized" in data:
                print_test("Scrub event", True)
                return data
            else:
                print_test("Scrub event", False, "Missing fields in response")
                return None
        else:
            print_test("Scrub event", False, f"Status {r.status_code}: {r.text}")
            return None
    except Exception as e:
        print_test("Scrub event", False, str(e))
        return None


def test_backend_draft(event_id, clean_text, production_mode=True):
    """Test backend draft generation."""
    print_section("Backend: Draft Generation")
    
    if not event_id or not clean_text:
        print_test("Generate draft (skipped)", False, "Missing event_id or clean_text")
        return None
    
    try:
        payload = {
            "event_id": event_id,
            "clean_text": clean_text,
            "production_mode": production_mode
        }
        r = requests.post(f"{BACKEND_URL}/api/v1/draft/generate", json=payload, timeout=60)
        
        if r.status_code == 200:
            data = r.json()
            if "text" in data and "citations" in data:
                print_test("Generate draft", True)
                print(f"    Draft length: {len(data['text'])} chars")
                print(f"    Citations: {len(data['citations'])}")
                return data
            else:
                print_test("Generate draft", False, "Missing fields in response")
                return None
        else:
            print_test("Generate draft", False, f"Status {r.status_code}: {r.text}")
            return None
    except Exception as e:
        print_test("Generate draft", False, str(e))
        return None


# ============================================================================
# SCOUT TESTS
# ============================================================================

def test_scout_events():
    """Test Scout events endpoint."""
    print_section("Scout: Events")
    
    try:
        # Test basic events endpoint
        r = requests.get(f"{SCOUT_URL}/scout/events?hours=24&limit=10", timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if "events" in data and "count" in data:
                print_test("GET /scout/events", True)
                print(f"    Found {data['count']} events")
                return data.get("events", [])
            else:
                print_test("GET /scout/events", False, "Missing fields")
                return []
        else:
            print_test("GET /scout/events", False, f"Status {r.status_code}")
            return []
    except Exception as e:
        print_test("GET /scout/events", False, str(e))
        return []


def test_scout_feeds():
    """Test Scout feeds endpoint."""
    print_section("Scout: Feeds")
    
    try:
        r = requests.get(f"{SCOUT_URL}/scout/feeds", timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if "feeds" in data:
                print_test("GET /scout/feeds", True)
                print(f"    Found {len(data['feeds'])} feeds")
                return data.get("feeds", [])
            else:
                print_test("GET /scout/feeds", False, "Missing feeds field")
                return []
        else:
            print_test("GET /scout/feeds", False, f"Status {r.status_code}")
            return []
    except Exception as e:
        print_test("GET /scout/feeds", False, str(e))
        return []


def test_scout_config_status():
    """Test Scout config status endpoint."""
    print_section("Scout: Config Status")
    
    try:
        r = requests.get(f"{SCOUT_URL}/scout/config/status", timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            required_fields = ["teams_configured", "notifications_enabled", "default_min_score", "feed_count"]
            if all(field in data for field in required_fields):
                print_test("GET /scout/config/status", True)
                print(f"    Teams configured: {data['teams_configured']}")
                print(f"    Notifications enabled: {data['notifications_enabled']}")
                print(f"    Default min score: {data['default_min_score']}")
                print(f"    Feed count: {data['feed_count']}")
                return data
            else:
                print_test("GET /scout/config/status", False, "Missing required fields")
                return None
        else:
            print_test("GET /scout/config/status", False, f"Status {r.status_code}")
            return None
    except Exception as e:
        print_test("GET /scout/config/status", False, str(e))
        return None


def test_scout_feed_crud():
    """Test Scout feed CRUD operations."""
    print_section("Scout: Feed CRUD")
    
    # Check if config write is allowed
    try:
        test_feed = {
            "name": f"Test Feed {uuid4().hex[:8]}",
            "url": "https://example.com/rss.xml",
            "poll_interval": 900,
            "score_threshold": 5
        }
        
        # Try to add feed
        r = requests.post(f"{SCOUT_URL}/scout/feeds", json=test_feed, timeout=10)
        
        if r.status_code == 200 or r.status_code == 201:
            data = r.json()
            feed_id = data.get("id")
            print_test("POST /scout/feeds (add)", True)
            
            if feed_id:
                # Test update
                update_payload = {"enabled": False}
                r2 = requests.patch(f"{SCOUT_URL}/scout/feeds/{feed_id}", json=update_payload, timeout=10)
                
                if r2.status_code == 200:
                    print_test("PATCH /scout/feeds/{id} (update)", True)
                else:
                    print_test("PATCH /scout/feeds/{id} (update)", False, f"Status {r2.status_code}")
                
                # Test delete
                r3 = requests.delete(f"{SCOUT_URL}/scout/feeds/{feed_id}", timeout=10)
                
                if r3.status_code == 200:
                    print_test("DELETE /scout/feeds/{id} (delete)", True)
                else:
                    print_test("DELETE /scout/feeds/{id} (delete)", False, f"Status {r3.status_code}")
            else:
                print_test("Feed CRUD (incomplete)", False, "No feed_id returned")
        elif r.status_code == 403:
            print_test("POST /scout/feeds (skipped)", True, "Config write not allowed (expected)")
        else:
            print_test("POST /scout/feeds", False, f"Status {r.status_code}: {r.text}")
    except Exception as e:
        print_test("Feed CRUD", False, str(e))


def test_scout_poll_now(feeds):
    """Test Scout poll now endpoint."""
    print_section("Scout: Poll Now")
    
    if not feeds:
        print_test("Poll now (skipped)", False, "No feeds available")
        return
    
    try:
        feed_id = feeds[0].get("id")
        if not feed_id:
            print_test("Poll now (skipped)", False, "No feed ID")
            return
        
        r = requests.post(f"{SCOUT_URL}/scout/feeds/{feed_id}/poll", timeout=60)
        
        if r.status_code == 200:
            data = r.json()
            if "ok" in data and "new_items" in data:
                print_test("POST /scout/feeds/{id}/poll", True)
                print(f"    New items: {data['new_items']}")
            else:
                print_test("POST /scout/feeds/{id}/poll", False, "Missing fields")
        else:
            print_test("POST /scout/feeds/{id}/poll", False, f"Status {r.status_code}")
    except Exception as e:
        print_test("Poll now", False, str(e))


def test_scout_notify(events):
    """Test Scout notification endpoint."""
    print_section("Scout: Notifications")
    
    if not events:
        print_test("Send notification (skipped)", False, "No events available")
        return
    
    try:
        event_id = events[0].get("event_id")
        if not event_id:
            print_test("Send notification (skipped)", False, "No event_id")
            return
        
        payload = {"event_id": event_id}
        r = requests.post(f"{SCOUT_URL}/scout/notify", json=payload, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if "ok" in data:
                if data["ok"]:
                    print_test("POST /scout/notify", True)
                else:
                    print_test("POST /scout/notify", False, data.get("error", "Unknown error"))
            else:
                print_test("POST /scout/notify", False, "Missing ok field")
        else:
            print_test("POST /scout/notify", False, f"Status {r.status_code}: {r.text}")
    except Exception as e:
        print_test("Send notification", False, str(e))


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_pipeline():
    """Test full pipeline: Ingest → Scrub → Draft."""
    print_section("Integration: Full Pipeline")
    
    # Step 1: Ingest
    event_id = test_backend_ingest()
    if not event_id:
        print_test("Full pipeline (failed)", False, "Ingest failed")
        return
    
    # Step 2: Scrub
    scrub_result = test_backend_scrub(event_id, production_mode=True)
    if not scrub_result:
        print_test("Full pipeline (failed)", False, "Scrub failed")
        return
    
    # Step 3: Draft
    draft_result = test_backend_draft(event_id, scrub_result["clean_text"], production_mode=True)
    if not draft_result:
        print_test("Full pipeline (failed)", False, "Draft generation failed")
        return
    
    print_test("Full pipeline", True)
    print(f"    Event ID: {event_id}")
    print(f"    Anonymized: {scrub_result['is_anonymized']}")
    print(f"    Draft citations: {len(draft_result['citations'])}")


def test_scout_to_backend_integration():
    """Test integration: Scout events → Backend pipeline."""
    print_section("Integration: Scout → Backend")
    
    # Get events from Scout
    events = test_scout_events()
    if not events:
        print_test("Scout → Backend (skipped)", False, "No events from Scout")
        return
    
    # Try to process first event
    event_id = events[0].get("event_id")
    if not event_id:
        print_test("Scout → Backend (skipped)", False, "No event_id")
        return
    
    # Try to scrub
    scrub_result = test_backend_scrub(event_id, production_mode=True)
    if scrub_result:
        print_test("Scout → Backend integration", True)
    else:
        print_test("Scout → Backend integration", False, "Could not scrub Scout event")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("  COPY/PASTE EXTENDED SYSTEM TEST")
    print("="*70)
    print(f"Started: {datetime.now()}")
    print(f"Backend: {BACKEND_URL}")
    print(f"Scout: {SCOUT_URL}")
    
    # Wait for services
    if not wait_for_services():
        print("\n❌ Services not available. Exiting.")
        sys.exit(1)
    
    # Backend tests
    event_id = test_backend_ingest()
    scrub_result = test_backend_scrub(event_id, production_mode=True) if event_id else None
    draft_result = None
    if scrub_result:
        draft_result = test_backend_draft(event_id, scrub_result["clean_text"], production_mode=True)
    
    # Scout tests
    events = test_scout_events()
    feeds = test_scout_feeds()
    config_status = test_scout_config_status()
    test_scout_feed_crud()
    if feeds:
        test_scout_poll_now(feeds)
    if events:
        test_scout_notify(events)
    
    # Integration tests
    test_full_pipeline()
    test_scout_to_backend_integration()
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {PASSED}")
    print(f"❌ Failed: {FAILED}")
    print(f"Total: {PASSED + FAILED}")
    
    if ERRORS:
        print("\nErrors:")
        for error in ERRORS:
            print(f"  - {error}")
    
    if FAILED > 0:
        print("\n❌ Some tests failed.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

