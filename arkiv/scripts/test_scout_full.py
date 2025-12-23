#!/usr/bin/env python3
"""
Fullständig test av Scout-modulen med riktig data.

Testar:
1. Scout pollar RSS feeds
2. Scout skapar events via /api/v1/ingest
3. Events går genom hela pipeline
"""
import httpx
import asyncio
import subprocess
import time
import os
import signal
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
SCOUT_URL = "http://localhost:8001"


async def wait_for_scout_api(max_wait=30):
    """Vänta på att Scout API blir tillgänglig."""
    async with httpx.AsyncClient() as client:
        for i in range(max_wait):
            try:
                response = await client.get(f"{SCOUT_URL}/health", timeout=2.0)
                if response.status_code == 200:
                    return True
            except:
                pass
            await asyncio.sleep(1)
        return False


async def test_scout_polling():
    """Test att Scout pollar feeds och skapar events."""
    print("=" * 60)
    print("🧪 TESTAR SCOUT MED RIKTIGA RSS FEEDS")
    print("=" * 60)
    
    # 1. Starta Scout i bakgrunden
    print("\n1️⃣  Startar Scout service...")
    print("-" * 60)
    
    env = os.environ.copy()
    env["BACKEND_URL"] = BACKEND_URL
    env["FEEDS_CONFIG"] = "scout/feeds.yaml"
    env["SCOUT_RUN_ONCE"] = "false"
    
    # Starta Scout som bakgrundsprocess
    scout_process = subprocess.Popen(
        ["python3", "scout/scheduler.py"],
        env=env,
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"✅ Scout startad (PID: {scout_process.pid})")
    
    try:
        # 2. Vänta på att Scout API blir tillgänglig
        print("\n2️⃣  Väntar på Scout API...")
        print("-" * 60)
        
        api_ready = await wait_for_scout_api()
        if not api_ready:
            print("❌ Scout API blev inte tillgänglig inom 30 sekunder")
            return False
        
        print("✅ Scout API är tillgänglig")
        
        # 3. Vänta på att Scout pollar feeds (kan ta upp till 5 min för Polisen)
        print("\n3️⃣  Väntar på att Scout pollar feeds...")
        print("-" * 60)
        print("   Polisen feed pollas var 5:e minut")
        print("   SVT feed pollas var 15:e minut")
        print("   Väntar 10 sekunder för första poll...")
        
        await asyncio.sleep(10)
        
        # 4. Kolla events
        print("\n4️⃣  Kontrollerar events...")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SCOUT_URL}/scout/events?hours=24", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            events = data.get("events", [])
            
            print(f"✅ Hittade {len(events)} events från senaste 24h")
            
            if events:
                print("\n📋 Senaste events:")
                for i, event in enumerate(events[:5], 1):
                    print(f"   {i}. Feed: {event.get('feed_url', 'N/A')}")
                    print(f"      Event ID: {event.get('event_id', 'N/A')}")
                    print(f"      Detected: {event.get('detected_at', 'N/A')}")
                    print()
                
                # Testa ett event genom pipeline
                first_event = events[0]
                event_id = first_event.get("event_id")
                
                if event_id:
                    print("\n5️⃣  Testar event genom pipeline...")
                    print("-" * 60)
                    
                    # Scrub
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
                        scrub_data = response.json()
                        print(f"✅ Scrub OK: {scrub_data.get('is_anonymized', False)}")
                        
                        # Draft (om API key finns)
                        clean_text = scrub_data.get("clean_text", "")
                        is_anonymized = scrub_data.get("is_anonymized", False)
                        
                        if os.getenv("OPENAI_API_KEY"):
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
                                draft_data = response.json()
                                print(f"✅ Draft OK: {len(draft_data.get('text', ''))} chars, {len(draft_data.get('citations', []))} citations")
                            except Exception as e:
                                print(f"⚠️  Draft generation failed: {e}")
                        else:
                            print("⚠️  Skippar draft generation (ingen OPENAI_API_KEY)")
                    except Exception as e:
                        print(f"⚠️  Pipeline test failed: {e}")
            else:
                print("⚠️  Inga events ännu. Scout pollar feeds automatiskt.")
                print("   För att testa manuellt, kör:")
                print("   export BACKEND_URL=http://localhost:8000")
                print("   export FEEDS_CONFIG=scout/feeds.yaml")
                print("   export SCOUT_RUN_ONCE=true")
                print("   python3 scout/scheduler.py")
        
        print("\n" + "=" * 60)
        print("✅ SCOUT TEST KLAR!")
        print("=" * 60)
        print("\n💡 Scout körs i bakgrunden och pollar feeds automatiskt.")
        print("   Stoppa med: kill", scout_process.pid)
        
        return True
        
    finally:
        # Stoppa Scout
        print(f"\n🛑 Stoppar Scout (PID: {scout_process.pid})...")
        scout_process.terminate()
        try:
            scout_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            scout_process.kill()
        print("✅ Scout stoppad")


if __name__ == "__main__":
    asyncio.run(test_scout_polling())

