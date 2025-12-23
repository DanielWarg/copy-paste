#!/usr/bin/env python3
"""Test med OpenAI API key från .env"""
import requests
import os

API_BASE = "http://localhost:8000"

# Load API key from .env
env_file = '.env'
api_key = None
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY=') and not line.startswith('OPENAI_API_KEY=#'):
                api_key = line.split('=', 1)[1].strip()
                if api_key:
                    break

print("="*60)
print("COPY/PASTE - TEST MED API KEY")
print("="*60)

if not api_key:
    print("❌ Ingen API key hittad i .env")
    print("   Kontrollera att OPENAI_API_KEY är satt i .env")
    exit(1)

print(f"✅ API key hittad: {api_key[:15]}...")

# Test full pipeline
print("\n1. Ingest...")
test_text = "John Doe arbetar på Acme Corporation i Stockholm. Kontakt: john.doe@acme.com, telefon 070-123 45 67. Adress: Storgatan 123."
r = requests.post(f"{API_BASE}/api/v1/ingest", json={"input_type": "text", "value": test_text}, timeout=10)
event_id = r.json()['event_id']
print(f"   ✅ Event ID: {event_id}")

print("\n2. Scrub...")
r2 = requests.post(f"{API_BASE}/api/v1/privacy/scrub", json={"event_id": event_id, "production_mode": True}, timeout=30)
clean_text = r2.json()['clean_text']
is_anonymized = r2.json()['is_anonymized']
print(f"   ✅ Is anonymized: {is_anonymized}")
print(f"   Clean text: {clean_text[:100]}...")

# Check PII
pii_items = ['john.doe@acme.com', '070-123 45 67', 'Storgatan 123']
leaked = [item for item in pii_items if item.lower() in clean_text.lower()]
if leaked:
    print(f"   🔴 PII LEAKED: {leaked}")
else:
    print(f"   ✅ No PII leaked")

print("\n3. Draft Generation...")
r3 = requests.post(
    f"{API_BASE}/api/v1/draft/generate",
    json={"event_id": event_id, "clean_text": clean_text, "production_mode": True},
    timeout=60
)

if r3.status_code == 200:
    draft = r3.json()
    print(f"   ✅ Draft generated!")
    print(f"   Text length: {len(draft.get('text', ''))} chars")
    print(f"   Citations: {len(draft.get('citations', []))}")
    print(f"   Policy violations: {draft.get('policy_violations', [])}")
    print(f"\n   Draft preview:")
    print(f"   {draft.get('text', '')[:300]}...")
    
    if draft.get('citations'):
        print(f"\n   Citations:")
        for cit in draft.get('citations', [])[:3]:
            print(f"   - {cit.get('id')}: {cit.get('excerpt', '')[:60]}...")
else:
    print(f"   ❌ Failed: {r3.status_code}")
    print(f"   Response: {r3.text[:200]}")

print("\n" + "="*60)
print("✅ TEST KLAR!")
print("="*60)

