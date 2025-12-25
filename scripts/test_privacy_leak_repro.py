#!/usr/bin/env python3
"""Reproducerbart test för Privacy Shield leak prevention edge case."""
import sys
import requests
import json

BACKEND_URL = "http://localhost:8000"

def test_leak_prevention_edge_case():
    """Test Privacy Shield med 100 repetitioner av PII."""
    print("Testing Privacy Shield leak prevention (100 repetitions)...")
    print()
    
    # Test 1: 100 repetitioner av email
    test_text = "test@example.com 070-1234567" * 100
    print(f"Test input length: {len(test_text)} characters")
    print(f"Expected: ~100 emails, ~100 phones")
    print()
    
    payload = {
        "text": test_text,
        "mode": "strict",
        "language": "sv"
    }
    
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/privacy/mask",
            json=payload,
            timeout=30
        )
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 422:
            print("✅ CORRECT: Request blocked (422) - leak detected")
            data = resp.json()
            print(f"Error: {data.get('detail', 'Unknown')}")
            return True
        
        elif resp.status_code == 200:
            data = resp.json()
            masked = data.get("maskedText", "")
            
            print(f"Output length: {len(masked)}")
            print(f"Contains [EMAIL]: {masked.count('[EMAIL]')}")
            print(f"Contains [PHONE]: {masked.count('[PHONE]')}")
            print()
            
            # Check for raw PII
            has_email = "@example.com" in masked or "test@example.com" in masked
            has_phone = "070-1234567" in masked or "0701234567" in masked
            
            if has_email or has_phone:
                print("❌ FAIL: Raw PII found in masked output!")
                if has_email:
                    # Find first occurrence
                    idx = masked.find("@example.com")
                    if idx >= 0:
                        start = max(0, idx - 50)
                        end = min(len(masked), idx + 100)
                        print(f"Found email at position {idx}:")
                        print(f"  ...{masked[start:end]}...")
                if has_phone:
                    idx = masked.find("070")
                    if idx >= 0:
                        start = max(0, idx - 50)
                        end = min(len(masked), idx + 100)
                        print(f"Found phone at position {idx}:")
                        print(f"  ...{masked[start:end]}...")
                return False
            else:
                print("✅ PASS: No raw PII in output")
                return True
        else:
            print(f"❌ UNEXPECTED STATUS: {resp.status_code}")
            print(resp.text[:500])
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_leak_prevention_edge_case()
    sys.exit(0 if success else 1)

