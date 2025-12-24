#!/usr/bin/env python3
"""
Test CORS from browser perspective - simulates what browser does.
"""
import requests
import json

SCOUT_URL = "http://localhost:8001"
FRONTEND_ORIGIN = "http://localhost:3000"

def test_cors_preflight():
    """Test OPTIONS preflight request (what browser does first)."""
    print("Testing OPTIONS preflight request...")
    response = requests.options(
        f"{SCOUT_URL}/scout/feeds",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"CORS Headers:")
    for header in ["access-control-allow-origin", "access-control-allow-methods", 
                   "access-control-allow-credentials", "access-control-max-age"]:
        value = response.headers.get(header, "NOT FOUND")
        print(f"  {header}: {value}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN, \
        f"Expected {FRONTEND_ORIGIN}, got {response.headers.get('access-control-allow-origin')}"
    assert response.headers.get("access-control-allow-credentials") == "true", \
        "Expected access-control-allow-credentials: true"
    print("✅ OPTIONS preflight OK\n")
    return True

def test_cors_get():
    """Test GET request with Origin header (what browser does after preflight)."""
    print("Testing GET request with Origin header...")
    response = requests.get(
        f"{SCOUT_URL}/scout/feeds",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Accept": "application/json"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"CORS Headers:")
    for header in ["access-control-allow-origin", "access-control-allow-credentials"]:
        value = response.headers.get(header, "NOT FOUND")
        print(f"  {header}: {value}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN, \
        f"Expected {FRONTEND_ORIGIN}, got {response.headers.get('access-control-allow-origin')}"
    assert response.headers.get("access-control-allow-credentials") == "true", \
        "Expected access-control-allow-credentials: true"
    
    # Verify response data
    data = response.json()
    assert "feeds" in data, "Response missing 'feeds' key"
    assert isinstance(data["feeds"], list), "feeds should be a list"
    print(f"✅ GET request OK - Received {len(data['feeds'])} feeds\n")
    return True

def test_cors_events():
    """Test GET /scout/events endpoint."""
    print("Testing GET /scout/events...")
    response = requests.get(
        f"{SCOUT_URL}/scout/events?hours=24",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Accept": "application/json"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"CORS Headers:")
    for header in ["access-control-allow-origin", "access-control-allow-credentials"]:
        value = response.headers.get(header, "NOT FOUND")
        print(f"  {header}: {value}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN, \
        f"Expected {FRONTEND_ORIGIN}, got {response.headers.get('access-control-allow-origin')}"
    
    data = response.json()
    assert "events" in data, "Response missing 'events' key"
    print(f"✅ GET /scout/events OK - Received {len(data.get('events', []))} events\n")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("CORS Browser Simulation Test")
    print("=" * 60)
    print()
    
    try:
        test_cors_preflight()
        test_cors_get()
        test_cors_events()
        
        print("=" * 60)
        print("✅ ALL CORS TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)

