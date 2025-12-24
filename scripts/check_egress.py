#!/usr/bin/env python3
"""Egress check - verify backend cannot reach external endpoints (production requirement)."""
import sys
import os
import socket
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings


def check_egress() -> dict:
    """Check if backend can reach external endpoints.
    
    In production, backend should NOT have internet egress.
    This script verifies that requirement.
    
    Returns:
        Dict with check results
    """
    test_endpoints = [
        ("example.com", 80),
        ("8.8.8.8", 53),  # Google DNS
    ]
    
    results = {
        "can_reach_external": False,
        "endpoints_tested": [],
        "errors": [],
    }
    
    for host, port in test_endpoints:
        try:
            # Try to connect (with short timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex((host, port))
            sock.close()
            
            reachable = result == 0
            results["endpoints_tested"].append({
                "host": host,
                "port": port,
                "reachable": reachable,
            })
            
            if reachable:
                results["can_reach_external"] = True
        except Exception as e:
            results["errors"].append({
                "host": host,
                "port": port,
                "error": str(e),
            })
    
    # In production, we EXPECT failure (no egress)
    if not settings.debug:
        if results["can_reach_external"]:
            results["status"] = "FAIL"
            results["message"] = (
                "SECURITY ISSUE: Backend can reach external endpoints. "
                "In production, backend must NOT have internet egress. "
                "This violates OPSEC policy. See docs/opsec.md"
            )
        else:
            results["status"] = "PASS"
            results["message"] = "Backend cannot reach external endpoints (as required in production)"
    else:
        # In dev mode, egress is allowed (for development)
        results["status"] = "INFO"
        results["message"] = "Development mode: egress check is informational only"
    
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("EGRESS CHECK")
    print("=" * 60)
    print()
    
    results = check_egress()
    
    print(f"Status: {results['status']}")
    print(f"Message: {results['message']}")
    print()
    
    if results["endpoints_tested"]:
        print("Endpoints tested:")
        for endpoint in results["endpoints_tested"]:
            status = "✓ REACHABLE" if endpoint["reachable"] else "✗ UNREACHABLE"
            print(f"  {endpoint['host']}:{endpoint['port']} - {status}")
    
    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  {error['host']}:{error['port']} - {error['error']}")
    
    print()
    print("=" * 60)
    
    if results["status"] == "FAIL":
        print("❌ EGRESS CHECK FAILED - SECURITY ISSUE")
        sys.exit(1)
    elif results["status"] == "PASS":
        print("✅ EGRESS CHECK PASSED")
        sys.exit(0)
    else:
        print("ℹ️  EGRESS CHECK (INFO MODE)")
        sys.exit(0)

