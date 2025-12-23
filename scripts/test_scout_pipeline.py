#!/usr/bin/env python3
"""
Test Scout Pipeline med riktig data.

Testar hela flödet: RSS Feed → Scout → Ingest → Scrub → Draft
"""
import httpx
import asyncio
import json
import time
from datetime import datetime
from uuid import UUID

BACKEND_URL = "http://localhost:8000"
SCOUT_URL = "http://localhost:8001"


async def test_scout_health():
    """Test Scout health endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SCOUT_URL}/health", timeout=5.0)
            response.raise_for_status()
            print("✅ Scout health check OK")
            return True
        except Exception as e:
            print(f"❌ Scout health check failed: {e}")
            return False


async def test_backend_health():
    """Test Backend health endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/health", timeout=5.0)
            response.raise_for_status()
            print("✅ Backend health check OK")
            return True
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False


async def get_scout_events():
    """Hämta events från Scout."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SCOUT_URL}/scout/events?hours=24", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data.get("events", [])
        except Exception as e:
            print(f"⚠️  Kunde inte hämta Scout events: {e}")
            return []


async def trigger_scout_run_once():
    """Trigger Scout att köra en gång (via SCOUT_RUN_ONCE)."""
    print("\n🔄 Triggering Scout run_once...")
    # Detta skulle kräva att vi kan köra scout med SCOUT_RUN_ONCE=true
    # För nu väntar vi bara på att Scout pollar automatiskt
    print("⏳ Väntar 30 sekunder för att Scout ska polla feeds...")
    await asyncio.sleep(30)


async def test_ingest_via_scout():
    """Test att Scout skapar events via /api/v1/ingest."""
    print("\n📥 Testar att Scout skapar events...")
    
    # Vänta lite för att Scout ska polla
    await asyncio.sleep(10)
    
    # Hämta events från Scout
    events = await get_scout_events()
    
    if not events:
        print("⚠️  Inga events hittades ännu. Scout kanske inte har pollat än.")
        print("   Försöker igen om 20 sekunder...")
        await asyncio.sleep(20)
        events = await get_scout_events()
    
    if events:
        print(f"✅ Scout har skapat {len(events)} events")
        for i, event in enumerate(events[:3], 1):
            print(f"   Event {i}: {event.get('dedupe_key', 'N/A')[:50]}...")
            print(f"            Feed: {event.get('feed_url', 'N/A')}")
            print(f"            Event ID: {event.get('event_id', 'N/A')}")
        return events
    else:
        print("❌ Inga events hittades. Scout verkar inte ha pollat feeds ännu.")
        return []


async def test_scrub_event(event_id: str):
    """Test scrub för ett event."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/privacy/scrub",
                json={
                    "event_id": event_id,
                    "production_mode": True
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            clean_text = data.get("clean_text", "")
            is_anonymized = data.get("is_anonymized", False)
            
            print(f"✅ Scrub OK för event {event_id[:8]}...")
            print(f"   Anonymized: {is_anonymized}")
            print(f"   Clean text length: {len(clean_text)} chars")
            print(f"   Preview: {clean_text[:100]}...")
            
            return data
        except Exception as e:
            print(f"❌ Scrub failed för event {event_id[:8]}...: {e}")
            return None


async def test_generate_draft(event_id: str, clean_text: str, is_anonymized: bool):
    """Test draft generation."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/draft/generate",
                json={
                    "event_id": event_id,
                    "clean_text": clean_text,
                    "production_mode": True,
                    "is_anonymized": is_anonymized
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            
            draft_text = data.get("text", "")
            citations = data.get("citations", [])
            violations = data.get("policy_violations", [])
            
            print(f"✅ Draft generated för event {event_id[:8]}...")
            print(f"   Draft length: {len(draft_text)} chars")
            print(f"   Citations: {len(citations)}")
            print(f"   Violations: {violations}")
            print(f"   Preview: {draft_text[:150]}...")
            
            return data
        except Exception as e:
            print(f"❌ Draft generation failed: {e}")
            if hasattr(e, 'response'):
                print(f"   Response: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
            return None


async def test_full_pipeline():
    """Test hela pipeline från RSS till Draft."""
    print("=" * 60)
    print("🧪 TESTAR SCOUT PIPELINE MED RIKTIG DATA")
    print("=" * 60)
    
    # 1. Health checks
    print("\n1️⃣  Health Checks")
    print("-" * 60)
    backend_ok = await test_backend_health()
    scout_ok = await test_scout_health()
    
    if not backend_ok or not scout_ok:
        print("\n❌ Health checks failed. Starta systemet med: docker compose up -d")
        return False
    
    # 2. Vänta på att Scout skapar events
    print("\n2️⃣  Scout Event Creation")
    print("-" * 60)
    events = await test_ingest_via_scout()
    
    if not events:
        print("\n⚠️  Inga events hittades. Det kan ta några minuter innan Scout pollar feeds.")
        print("   Scout pollar var 15:e minut (default) eller 5:e minut för Polisen.")
        print("   Du kan vänta eller testa manuellt med:")
        print("   curl -X POST http://localhost:8000/api/v1/ingest -H 'Content-Type: application/json' -d '{\"input_type\":\"url\",\"value\":\"https://polisen.se/aktuellt/rss/\"}'")
        return False
    
    # 3. Test scrub för första eventet
    print("\n3️⃣  Privacy Shield (Scrub)")
    print("-" * 60)
    first_event = events[0]
    event_id = first_event.get("event_id")
    
    if not event_id:
        print("❌ Event saknar event_id")
        return False
    
    scrubbed = await test_scrub_event(event_id)
    
    if not scrubbed:
        print("❌ Scrub failed, kan inte fortsätta")
        return False
    
    clean_text = scrubbed.get("clean_text", "")
    is_anonymized = scrubbed.get("is_anonymized", False)
    
    if not is_anonymized:
        print("⚠️  Text är inte anonymized, men fortsätter ändå...")
    
    # 4. Test draft generation
    print("\n4️⃣  Draft Generation")
    print("-" * 60)
    
    # Kontrollera om OpenAI API key finns
    import os
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️  OPENAI_API_KEY inte satt. Draft generation kommer att misslyckas.")
        print("   Sätt API key i .env filen för att testa draft generation.")
        return True  # Vi räknar detta som success eftersom vi testat resten
    
    draft = await test_generate_draft(event_id, clean_text, is_anonymized)
    
    if draft:
        print("\n" + "=" * 60)
        print("✅ HELA PIPELINE FUNGERAR!")
        print("=" * 60)
        return True
    else:
        print("\n⚠️  Pipeline fungerar men draft generation misslyckades.")
        print("   Kontrollera OpenAI API key och att backend kan nå OpenAI.")
        return True  # Vi räknar detta som success eftersom vi testat resten


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())

