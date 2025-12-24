#!/usr/bin/env python3
"""Debug script - test each step individually with timing."""
import sys
import time
import urllib.request
import json

def test_step(name, func):
    print(f"\n=== {name} ===", flush=True)
    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        print(f"✅ {name} OK ({elapsed:.2f}s)", flush=True)
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {name} FAILED ({elapsed:.2f}s): {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None

# Step 1: Health check
def health_check():
    req = urllib.request.Request('http://localhost:8000/health')
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read().decode())

# Step 2: Ingest
def ingest():
    data = json.dumps({
        'input_type': 'text',
        'value': 'Test text utan PII.',
        'metadata': {'test': 'debug'}
    }).encode()
    req = urllib.request.Request(
        'http://localhost:8000/api/v1/ingest',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode())

# Step 3: Scrub v2
def scrub_v2(event_id):
    data = json.dumps({
        'event_id': event_id,
        'production_mode': False,
        'max_retries': 1
    }).encode()
    req = urllib.request.Request(
        'http://localhost:8000/api/v1/privacy/scrub_v2',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read().decode())

print("Starting debug test...", flush=True)

# Test each step
health = test_step("Health Check", health_check)
if not health:
    sys.exit(1)

ingest_result = test_step("Ingest", ingest)
if not ingest_result:
    sys.exit(1)

event_id = ingest_result.get('event_id')
if not event_id:
    print("❌ No event_id in ingest response")
    sys.exit(1)

print(f"Event ID: {event_id}", flush=True)

scrub_result = test_step("Scrub V2", lambda: scrub_v2(event_id))
if not scrub_result:
    sys.exit(1)

print(f"\n✅ All steps completed!", flush=True)
print(f"Scrub result keys: {list(scrub_result.keys())}", flush=True)

