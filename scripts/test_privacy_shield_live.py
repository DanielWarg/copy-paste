#!/usr/bin/env python3
"""Live test script for Privacy Shield module - tests with real data."""
import json
import requests
import sys
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def test_mask(text: str, mode: str = "balanced", expected_tokens: list = None) -> Dict[str, Any]:
    """Test mask endpoint with real data."""
    print(f"\n=== Testing mask (mode={mode}) ===")
    print(f"Input: {text[:100]}...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/privacy/mask",
        json={
            "text": text,
            "mode": mode,
            "language": "sv"
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return {"success": False, "status": response.status_code}
    
    data = response.json()
    masked_text = data.get("maskedText", "")
    entities = data.get("entities", {})
    privacy_logs = data.get("privacyLogs", [])
    
    print(f"Masked: {masked_text[:100]}...")
    print(f"Entities: {entities}")
    log_str = ", ".join([f"{log['rule']}:{log['count']}" for log in privacy_logs])
    print(f"Privacy logs: {log_str}")
    
    # Verify tokens
    if expected_tokens:
        for token in expected_tokens:
            if token not in masked_text:
                print(f"⚠️  Warning: Expected token {token} not found in masked text")
            else:
                print(f"✅ Found token: {token}")
    
    # Verify no PII in masked text
    pii_patterns = ["@", "070-", "800101", "12345"]
    found_pii = []
    for pattern in pii_patterns:
        if pattern in masked_text.lower():
            found_pii.append(pattern)
    
    if found_pii:
        print(f"⚠️  Warning: Potential PII found in masked text: {found_pii}")
        return {"success": False, "found_pii": found_pii}
    else:
        print("✅ No PII patterns found in masked text")
    
    return {"success": True, "data": data}


def main() -> int:
    """Run live tests."""
    print("Privacy Shield Live Tests")
    print("=" * 50)
    
    # Test 1: Email
    result1 = test_mask(
        "Kontakta mig på test@example.com",
        expected_tokens=["[EMAIL]"]
    )
    if not result1["success"]:
        return 1
    
    # Test 2: Phone
    result2 = test_mask(
        "Ring mig på 070-123 45 67",
        expected_tokens=["[PHONE]"]
    )
    if not result2["success"]:
        return 1
    
    # Test 3: Personnummer
    result3 = test_mask(
        "Personnummer: 800101-1234",
        expected_tokens=["[PNR]"]
    )
    if not result3["success"]:
        return 1
    
    # Test 4: Combined PII
    result4 = test_mask(
        "Kontakta test@example.com eller ring 070-123 45 67. PNR: 800101-1234. Adress: Storgatan 42, 12345 Stockholm.",
        expected_tokens=["[EMAIL]", "[PHONE]", "[PNR]"]
    )
    if not result4["success"]:
        return 1
    
    # Test 5: Multiple emails
    result5 = test_mask(
        "Kontakta test@example.com eller admin@site.se",
        expected_tokens=["[EMAIL]"]
    )
    if not result5["success"]:
        return 1
    
    # Test 6: Phone variations
    result6 = test_mask(
        "Ring +46 70 123 45 67 eller 08-123 45 67",
        expected_tokens=["[PHONE]"]
    )
    if not result6["success"]:
        return 1
    
    # Test 7: Strict mode
    result7 = test_mask(
        "Kontakta test@example.com",
        mode="strict",
        expected_tokens=["[EMAIL]"]
    )
    if not result7["success"]:
        return 1
    
    # Test 8: No PII
    result8 = test_mask(
        "Detta är en vanlig text utan PII"
    )
    if not result8["success"]:
        return 1
    
    # Test 9: Large text (but within limit)
    large_text = "Detta är en lång text. " * 1000 + "Kontakta test@example.com"
    result9 = test_mask(large_text, expected_tokens=["[EMAIL]"])
    if not result9["success"]:
        return 1
    
    # Test 10: Edge case - email in middle
    result10 = test_mask(
        "Hej, mitt namn är Kalle och min email är test@example.com, ring mig gärna!",
        expected_tokens=["[EMAIL]"]
    )
    if not result10["success"]:
        return 1
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend. Is it running?")
        print("Start with: docker-compose up -d backend")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

