#!/usr/bin/env python3
"""
Manuell test av RSS feed → Ingest → Scrub → Draft pipeline.
Använder riktig RSS feed från Polisen.
"""
import httpx
import asyncio
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"


async def test_rss_to_draft():
    """Test hela pipeline med riktig RSS feed."""
    print("=" * 60)
    print("🧪 TESTAR RSS → INGEST → SCRUB → DRAFT")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Ingest RSS feed URL
        print("\n1️⃣  Ingest RSS Feed URL")
        print("-" * 60)
        
        rss_url = "https://polisen.se/aktuellt/rss/"
        print(f"📥 Hämtar RSS feed från: {rss_url}")
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/ingest",
                json={
                    "input_type": "url",
                    "value": rss_url,
                    "metadata": {
                        "scout_source": "Polisen",
                        "scout_feed_url": rss_url,
                        "scout_detected_at": datetime.utcnow().isoformat()
                    }
                }
            )
            response.raise_for_status()
            ingest_data = response.json()
            event_id = ingest_data.get("event_id")
            
            print(f"✅ Event skapat: {event_id}")
            print(f"   Status: {ingest_data.get('status')}")
            
        except Exception as e:
            print(f"❌ Ingest failed: {e}")
            return False
        
        # 2. Scrub
        print("\n2️⃣  Privacy Shield (Scrub)")
        print("-" * 60)
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/privacy/scrub",
                json={
                    "event_id": event_id,
                    "production_mode": True
                }
            )
            response.raise_for_status()
            scrub_data = response.json()
            
            clean_text = scrub_data.get("clean_text", "")
            is_anonymized = scrub_data.get("is_anonymized", False)
            
            print(f"✅ Scrub OK")
            print(f"   Anonymized: {is_anonymized}")
            print(f"   Clean text length: {len(clean_text)} chars")
            print(f"   Preview: {clean_text[:200]}...")
            
        except Exception as e:
            print(f"❌ Scrub failed: {e}")
            if hasattr(e, 'response'):
                print(f"   Response: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
            return False
        
        # 3. Draft Generation
        print("\n3️⃣  Draft Generation")
        print("-" * 60)
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/draft/generate",
                json={
                    "event_id": event_id,
                    "clean_text": clean_text,
                    "production_mode": True,
                    "is_anonymized": is_anonymized
                }
            )
            response.raise_for_status()
            draft_data = response.json()
            
            draft_text = draft_data.get("text", "")
            citations = draft_data.get("citations", [])
            violations = draft_data.get("policy_violations", [])
            
            print(f"✅ Draft generated")
            print(f"   Draft length: {len(draft_text)} chars")
            print(f"   Citations: {len(citations)}")
            print(f"   Violations: {violations}")
            print(f"\n📝 Draft Preview:")
            print("-" * 60)
            print(draft_text[:500])
            if len(draft_text) > 500:
                print("...")
            print("-" * 60)
            
            if citations:
                print(f"\n📚 Citations:")
                for i, citation in enumerate(citations[:3], 1):
                    print(f"   {i}. [{citation.get('id')}] {citation.get('excerpt', '')[:100]}...")
            
            print("\n" + "=" * 60)
            print("✅ HELA PIPELINE FUNGERAR MED RIKTIG DATA!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"❌ Draft generation failed: {e}")
            if hasattr(e, 'response'):
                print(f"   Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
                print(f"   Response: {e.response.text[:500] if hasattr(e.response, 'text') else 'N/A'}")
            
            # Kontrollera om det är API key problem
            import os
            if not os.getenv("OPENAI_API_KEY"):
                print("\n⚠️  OPENAI_API_KEY inte satt i miljön.")
                print("   Sätt API key i .env filen för att testa draft generation.")
            
            return False


if __name__ == "__main__":
    asyncio.run(test_rss_to_draft())

