#!/usr/bin/env python3
"""
LIVE TEST - Full Pipeline Test med Riktig Data
Testar: Ingest → Scrub → Draft (om API key finns)
"""
import requests
import json
import sys
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)

def test_health():
    """Test 1: Health Check"""
    print_section("TEST 1: Health Check")
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        if r.status_code == 200:
            print("✅ Backend server är online")
            print(f"   Response: {r.json()}")
            return True
        else:
            print(f"❌ Health check failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server inte tillgänglig: {e}")
        return False

def test_ingest():
    """Test 2: Ingest Text"""
    print_section("TEST 2: Ingest Text")
    
    test_text = """
    John Doe arbetar på Acme Corporation i Stockholm.
    Kontaktinformation: john.doe@acme.com, telefon 070-123 45 67.
    Adress: Storgatan 123, 111 22 Stockholm.
    """
    
    try:
        r = requests.post(
            f"{API_BASE}/api/v1/ingest",
            json={"input_type": "text", "value": test_text},
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            event_id = data.get("event_id")
            print(f"✅ Event skapad")
            print(f"   Event ID: {event_id}")
            print(f"   Status: {data.get('status')}")
            return event_id
        else:
            print(f"❌ Ingest failed: {r.status_code}")
            print(f"   Response: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_scrub(event_id, production_mode=True):
    """Test 3: Scrub (Anonymisering)"""
    print_section(f"TEST 3: Scrub (Production Mode: {'ON' if production_mode else 'OFF'})")
    
    try:
        r = requests.post(
            f"{API_BASE}/api/v1/privacy/scrub",
            json={"event_id": event_id, "production_mode": production_mode},
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            clean_text = data.get("clean_text", "")
            is_anonymized = data.get("is_anonymized", False)
            
            print(f"✅ Scrub completed")
            print(f"   Is anonymized: {is_anonymized}")
            print(f"\n   Original text preview:")
            print(f"   'John Doe arbetar på Acme Corporation...'")
            print(f"\n   Clean text preview:")
            print(f"   '{clean_text[:150]}...'")
            
            # Check for anonymization tokens
            has_tokens = any(t in clean_text for t in ["[PERSON", "[ORG", "[EMAIL", "[PHONE", "[ADDRESS"])
            if has_tokens:
                print(f"\n   ✅ Anonymization tokens found: {[t for t in ['[PERSON', '[ORG', '[EMAIL', '[PHONE', '[ADDRESS'] if t in clean_text]}")
            else:
                print(f"\n   ⚠️  No anonymization tokens found (text might be clean)")
            
            # Check for PII leakage
            pii_patterns = ["john.doe@acme.com", "070-123 45 67", "Storgatan 123"]
            leaked = [pii for pii in pii_patterns if pii.lower() in clean_text.lower()]
            if leaked:
                print(f"\n   🔴 PII LEAKED: {leaked}")
            else:
                print(f"\n   ✅ No PII leaked")
            
            return clean_text, is_anonymized
        else:
            print(f"❌ Scrub failed: {r.status_code}")
            print(f"   Response: {r.text}")
            return None, False
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, False

def test_draft_generation(event_id, clean_text, production_mode=True):
    """Test 4: Draft Generation"""
    print_section("TEST 4: Draft Generation")
    
    import os
    # Try to load from .env file
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key and os.path.exists(env_file):
        # Try to read from .env file
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        if api_key:
                            os.environ['OPENAI_API_KEY'] = api_key
                            break
        except:
            pass
    
    if not api_key:
        print("⚠️  OpenAI API key inte satt")
        print("   Draft generation kommer att skippas")
        print("   Sätt OPENAI_API_KEY i .env för att testa draft generation")
        return None
    
    try:
        r = requests.post(
            f"{API_BASE}/api/v1/draft/generate",
            json={
                "event_id": event_id,
                "clean_text": clean_text,
                "production_mode": production_mode
            },
            timeout=60
        )
        
        if r.status_code == 200:
            data = r.json()
            draft_text = data.get("text", "")
            citations = data.get("citations", [])
            violations = data.get("policy_violations", [])
            
            print(f"✅ Draft generated")
            print(f"   Draft length: {len(draft_text)} chars")
            print(f"   Citations: {len(citations)}")
            print(f"   Policy violations: {violations}")
            print(f"\n   Draft preview:")
            print(f"   {draft_text[:200]}...")
            
            if citations:
                print(f"\n   Citations:")
                for cit in citations[:3]:
                    print(f"   - {cit.get('id')}: {cit.get('excerpt', '')[:50]}...")
            
            return draft_text
        else:
            print(f"❌ Draft generation failed: {r.status_code}")
            print(f"   Response: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_security():
    """Test 5: Security Check"""
    print_section("TEST 5: Security Check")
    
    # Try to send unscrubbed data
    try:
        r = requests.post(
            f"{API_BASE}/api/v1/draft/generate",
            json={
                "event_id": "00000000-0000-0000-0000-000000000000",
                "clean_text": "John Doe email@test.com 555-1234",  # Unscrubbed!
                "production_mode": False
            },
            timeout=10
        )
        
        if r.status_code == 400:
            print("✅ Security check PASSED")
            print(f"   Unscrubbed data correctly blocked (HTTP 400)")
            print(f"   Message: {r.json().get('detail', '')}")
            return True
        else:
            print(f"🔴 Security check FAILED")
            print(f"   Expected HTTP 400, got {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all live tests"""
    print("="*60)
    print("COPY/PASTE - LIVE TEST")
    print("="*60)
    print(f"Started: {datetime.now()}")
    print(f"API Base: {API_BASE}")
    
    results = {
        "health": False,
        "ingest": False,
        "scrub": False,
        "draft": False,
        "security": False
    }
    
    # Test 1: Health
    results["health"] = test_health()
    if not results["health"]:
        print("\n❌ Server inte tillgänglig. Avbryter tester.")
        return 1
    
    # Test 2: Ingest
    event_id = test_ingest()
    if event_id:
        results["ingest"] = True
        
        # Test 3: Scrub
        clean_text, is_anonymized = test_scrub(event_id, production_mode=True)
        if clean_text:
            results["scrub"] = True
            
            # Test 4: Draft (if API key available)
            draft = test_draft_generation(event_id, clean_text, production_mode=True)
            if draft:
                results["draft"] = True
    
    # Test 5: Security
    results["security"] = test_security()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test.upper():15} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALLA TESTER PASSERADE!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) misslyckades")
        return 1

if __name__ == "__main__":
    sys.exit(main())

