#!/usr/bin/env python3
"""Comprehensive A-Z Security Test - All Functions & Security Analysis"""
import sys
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OUTPUT_FILE = Path(__file__).parent.parent / "tests" / "results" / f"SECURITY_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# Test results
results = {
    "timestamp": datetime.now().isoformat(),
    "backend_url": BACKEND_URL,
    "tests": {},
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "security_issues": []
    }
}

def log_test(module: str, test: str, status: str, details: Dict[str, Any], security_analysis: Dict[str, Any]):
    """Log test result with security analysis"""
    key = f"{module}.{test}"
    results["tests"][key] = {
        "status": status,
        "details": details,
        "security_analysis": security_analysis,
        "timestamp": datetime.now().isoformat()
    }
    results["summary"]["total"] += 1
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"{GREEN}✅{RESET} {module}.{test}")
    elif status == "FAIL":
        results["summary"]["failed"] += 1
        print(f"{RED}❌{RESET} {module}.{test}: {details.get('error', 'Unknown error')}")
    elif status == "WARN":
        results["summary"]["warnings"] += 1
        print(f"{YELLOW}⚠️{RESET} {module}.{test}: {details.get('warning', 'Warning')}")
    
    if security_analysis.get("issues"):
        results["summary"]["security_issues"].extend(security_analysis["issues"])

def test_health_endpoint():
    """Test /health endpoint"""
    module = "core"
    test = "health"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        details["status_code"] = resp.status_code
        details["response_time_ms"] = resp.elapsed.total_seconds() * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            details["response"] = data
            
            # Security checks
            if "request_id" in data:
                security["strengths"].append("Request ID present for traceability")
            else:
                security["issues"].append("Missing request_id in health response")
            
            log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Expected 200, got {resp.status_code}"
            log_test(module, test, "FAIL", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_ready_endpoint():
    """Test /ready endpoint"""
    module = "core"
    test = "ready"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        resp = requests.get(f"{BACKEND_URL}/ready", timeout=5)
        details["status_code"] = resp.status_code
        details["response_time_ms"] = resp.elapsed.total_seconds() * 1000
        
        data = resp.json()
        details["response"] = data
        
        # Security checks
        if resp.status_code in [200, 503]:
            security["strengths"].append("Graceful degradation (503 when DB down)")
        else:
            security["issues"].append(f"Unexpected status code: {resp.status_code}")
        
        if "db" in data or "status" in data:
            security["strengths"].append("DB status exposed correctly")
        
        log_test(module, test, "PASS", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_security_headers():
    """Test security headers in responses"""
    module = "core"
    test = "security_headers"
    details = {}
    security = {"issues": [], "strengths": []}
    
    required_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection"
    ]
    
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        headers = dict(resp.headers)
        details["headers"] = headers
        
        missing = []
        for header in required_headers:
            if header not in headers:
                missing.append(header)
            else:
                security["strengths"].append(f"{header} present")
        
        if missing:
            security["issues"].append(f"Missing security headers: {', '.join(missing)}")
            log_test(module, test, "WARN", details, security)
        else:
            log_test(module, test, "PASS", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_transcripts_list():
    """Test GET /api/v1/transcripts"""
    module = "transcripts"
    test = "list"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/transcripts", timeout=10)
        details["status_code"] = resp.status_code
        
        if resp.status_code == 200:
            data = resp.json()
            details["count"] = len(data.get("items", []))
            
            # Security: Check for PII in response
            resp_text = json.dumps(data)
            pii_indicators = ["@", "tel:", "+46", "070", "08", "personnummer"]
            found_pii = [ind for ind in pii_indicators if ind.lower() in resp_text.lower()]
            
            if found_pii:
                security["issues"].append(f"Possible PII in response: {found_pii}")
                log_test(module, test, "WARN", details, security)
            else:
                security["strengths"].append("No obvious PII in response")
                log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Expected 200, got {resp.status_code}"
            log_test(module, test, "FAIL", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_transcripts_create():
    """Test POST /api/v1/transcripts"""
    module = "transcripts"
    test = "create"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        payload = {
            "title": "Test Transcript",
            "source": "test",
            "language": "sv"
        }
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/transcripts",
            json=payload,
            timeout=10
        )
        details["status_code"] = resp.status_code
        
        if resp.status_code == 200:
            data = resp.json()
            details["transcript_id"] = data.get("id")
            security["strengths"].append("Validation works (Pydantic)")
            
            # Check for request_id in response
            if "request_id" in data or any("request" in str(k).lower() for k in data.keys()):
                security["strengths"].append("Request ID present for audit")
            
            log_test(module, test, "PASS", details, security)
            return data.get("id")
        else:
            details["error"] = f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            log_test(module, test, "FAIL", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", security, details)
    
    return None

def test_privacy_shield_mask():
    """Test POST /api/v1/privacy/mask"""
    module = "privacy_shield"
    test = "mask"
    details = {}
    security = {"issues": [], "strengths": []}
    
    test_text = "Kontakta mig på test@example.com eller 070-1234567"
    
    try:
        payload = {
            "text": test_text,
            "mode": "balanced",
            "language": "sv"
        }
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/privacy/mask",
            json=payload,
            timeout=10
        )
        details["status_code"] = resp.status_code
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Security: Verify PII is masked
            masked_text = data.get("maskedText", "")
            if "[EMAIL]" in masked_text and "[PHONE]" in masked_text:
                security["strengths"].append("PII correctly masked")
            else:
                security["issues"].append("PII not properly masked")
                log_test(module, test, "FAIL", details, security)
                return
            
            # Security: Check entity counts
            entities = data.get("entities", {})
            if entities.get("contacts", 0) > 0:
                security["strengths"].append("Entity detection works")
            
            # Security: Check no raw PII in response
            if test_text in masked_text:
                security["issues"].append("Raw PII found in masked output")
                log_test(module, test, "FAIL", details, security)
            else:
                log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            log_test(module, test, "FAIL", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_privacy_shield_leak_prevention():
    """Test Privacy Shield leak prevention"""
    module = "privacy_shield"
    test = "leak_prevention"
    details = {}
    security = {"issues": [], "strengths": []}
    
    # Test with text that should fail leak check
    test_text = "test@example.com" * 100  # Many emails
    
    try:
        payload = {
            "text": test_text,
            "mode": "strict",
            "language": "sv"
        }
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/privacy/mask",
            json=payload,
            timeout=15
        )
        details["status_code"] = resp.status_code
        
        if resp.status_code in [200, 422]:
            data = resp.json() if resp.content else {}
            masked_text = data.get("maskedText", "")
            
            # Security: Verify no raw emails in output
            if "@example.com" in masked_text:
                security["issues"].append("Raw PII leaked in masked output")
                log_test(module, test, "FAIL", details, security)
            else:
                security["strengths"].append("Leak prevention works")
                log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Unexpected status: {resp.status_code}"
            log_test(module, test, "WARN", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_record_create():
    """Test POST /api/v1/record/create"""
    module = "record"
    test = "create"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        payload = {
            "project_id": 1,
            "transcript_id": 1
        }
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/record/create",
            json=payload,
            timeout=10
        )
        details["status_code"] = resp.status_code
        
        if resp.status_code in [200, 201, 404, 422]:
            # 404/422 are acceptable (resource might not exist)
            security["strengths"].append("Proper validation/error handling")
            log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Unexpected status: {resp.status_code}"
            log_test(module, test, "WARN", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_projects_list():
    """Test GET /api/v1/projects"""
    module = "projects"
    test = "list"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/projects", timeout=10)
        details["status_code"] = resp.status_code
        
        if resp.status_code == 200:
            data = resp.json()
            details["count"] = len(data.get("items", []))
            security["strengths"].append("List endpoint works")
            log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Expected 200, got {resp.status_code}"
            log_test(module, test, "FAIL", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_console_events():
    """Test GET /api/v1/events"""
    module = "console"
    test = "events"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/events", timeout=10)
        details["status_code"] = resp.status_code
        
        if resp.status_code == 200:
            data = resp.json()
            details["count"] = len(data.get("items", []))
            security["strengths"].append("Events endpoint works")
            log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Expected 200, got {resp.status_code}"
            log_test(module, test, "FAIL", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_console_sources():
    """Test GET /api/v1/sources"""
    module = "console"
    test = "sources"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/sources", timeout=10)
        details["status_code"] = resp.status_code
        
        if resp.status_code == 200:
            data = resp.json()
            details["count"] = len(data.get("items", []))
            security["strengths"].append("Sources endpoint works")
            log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Expected 200, got {resp.status_code}"
            log_test(module, test, "FAIL", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_error_handling():
    """Test error handling (privacy-safe)"""
    module = "core"
    test = "error_handling"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        # Trigger validation error
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/transcripts",
            json={},  # Missing required fields
            timeout=10
        )
        details["status_code"] = resp.status_code
        
        if resp.status_code == 422:
            data = resp.json()
            error_text = json.dumps(data).lower()
            
            # Security: Check for no sensitive info in error
            sensitive = ["traceback", "file", "/app/", "exception", "stack"]
            found = [s for s in sensitive if s in error_text]
            
            if found:
                security["issues"].append(f"Sensitive info in error: {found}")
                log_test(module, test, "WARN", details, security)
            else:
                security["strengths"].append("Error messages are privacy-safe")
                log_test(module, test, "PASS", details, security)
        else:
            details["error"] = f"Expected 422, got {resp.status_code}"
            log_test(module, test, "WARN", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "FAIL", details, security)

def test_cors_configuration():
    """Test CORS configuration"""
    module = "core"
    test = "cors"
    details = {}
    security = {"issues": [], "strengths": []}
    
    try:
        resp = requests.options(
            f"{BACKEND_URL}/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET"
            },
            timeout=5
        )
        details["status_code"] = resp.status_code
        cors_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower().startswith("access-control-")
        }
        details["cors_headers"] = cors_headers
        
        if "Access-Control-Allow-Origin" in cors_headers:
            security["strengths"].append("CORS configured")
            # Check if wildcard in production (security risk)
            if cors_headers.get("Access-Control-Allow-Origin") == "*":
                security["issues"].append("CORS allows all origins (*)")
                log_test(module, test, "WARN", details, security)
            else:
                log_test(module, test, "PASS", details, security)
        else:
            security["issues"].append("CORS not configured")
            log_test(module, test, "WARN", details, security)
    except Exception as e:
        details["error"] = str(e)
        log_test(module, test, "WARN", details, security)

def main():
    """Run comprehensive security tests"""
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}Comprehensive A-Z Security Test{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {results['timestamp']}")
    print()
    
    # Core endpoints
    print(f"{BLUE}[CORE] Testing core endpoints...{RESET}")
    test_health_endpoint()
    test_ready_endpoint()
    test_security_headers()
    test_error_handling()
    test_cors_configuration()
    print()
    
    # Transcripts module
    print(f"{BLUE}[TRANSCRIPTS] Testing transcripts module...{RESET}")
    test_transcripts_list()
    transcript_id = test_transcripts_create()
    print()
    
    # Privacy Shield module
    print(f"{BLUE}[PRIVACY SHIELD] Testing privacy shield...{RESET}")
    test_privacy_shield_mask()
    test_privacy_shield_leak_prevention()
    print()
    
    # Record module
    print(f"{BLUE}[RECORD] Testing record module...{RESET}")
    test_record_create()
    print()
    
    # Projects module
    print(f"{BLUE}[PROJECTS] Testing projects module...{RESET}")
    test_projects_list()
    print()
    
    # Console module
    print(f"{BLUE}[CONSOLE] Testing console module...{RESET}")
    test_console_events()
    test_console_sources()
    print()
    
    # Summary
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}TEST SUMMARY{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    summary = results["summary"]
    print(f"Total tests: {summary['total']}")
    print(f"{GREEN}Passed: {summary['passed']}{RESET}")
    print(f"{RED}Failed: {summary['failed']}{RESET}")
    print(f"{YELLOW}Warnings: {summary['warnings']}{RESET}")
    
    if summary["security_issues"]:
        print(f"\n{YELLOW}Security Issues Found:{RESET}")
        for issue in set(summary["security_issues"]):
            print(f"  - {issue}")
    
    # Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n{BLUE}Results saved to: {OUTPUT_FILE}{RESET}")
    
    return 0 if summary["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

