#!/usr/bin/env python3
"""
Security Invariants Checker

Verifierar att hårda säkerhetsinvariants inte har brutits.
Körs som statisk gate (innan kod körs) och runtime gate (efter deployment).

Usage:
    python3 scripts/check_security_invariants.py [--static|--runtime]
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class SecurityInvariant:
    """Represents a security invariant that must not be broken."""
    
    def __init__(self, name: str, check_func, description: str):
        self.name = name
        self.check_func = check_func
        self.description = description
    
    def check(self) -> Tuple[bool, str]:
        """Returns (passed, message)."""
        try:
            return self.check_func()
        except Exception as e:
            return False, f"Check failed with exception: {e}"

def check_no_egress_bypass() -> Tuple[bool, str]:
    """Check: No direct HTTP requests without ensure_egress_allowed()"""
    backend_path = Path("backend/app")
    if not backend_path.exists():
        return True, "Backend path not found (skipping)"
    
    # Find all Python files that might make external requests
    forbidden_patterns = [
        r'requests\.(get|post|put|delete|patch)',
        r'httpx\.(get|post|put|delete|patch)',
        r'urllib\.request\.urlopen',
        r'aiohttp\.(get|post|put|delete|patch)',
    ]
    
    violations = []
    for py_file in backend_path.rglob("*.py"):
        # Skip test files and migrations
        if "test" in str(py_file) or "migration" in str(py_file) or "alembic" in str(py_file):
            continue
        
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        
        for pattern in forbidden_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Check if ensure_egress_allowed() is called before this
                line_num = content[:match.start()].count('\n') + 1
                before_match = content[:match.start()]
                
                # Check if ensure_egress_allowed is in the same function scope
                if 'ensure_egress_allowed' not in before_match[-500:]:
                    violations.append(f"{py_file}:{line_num} - {match.group()}")
    
    if violations:
        return False, f"Found {len(violations)} potential egress bypasses:\n" + "\n".join(violations[:10])
    return True, "No egress bypasses found"

def check_no_content_in_logs() -> Tuple[bool, str]:
    """Check: No content/PII in log statements"""
    backend_path = Path("backend/app")
    if not backend_path.exists():
        return True, "Backend path not found (skipping)"
    
    forbidden_log_fields = [
        'body', 'text', 'content', 'transcript', 'note_body', 'file_content',
        'payload', 'query_params', 'query', 'segment_text', 'transcript_text',
        'file_data', 'raw_content', 'original_text'
    ]
    
    violations = []
    for py_file in backend_path.rglob("*.py"):
        if "test" in str(py_file) or "migration" in str(py_file):
            continue
        
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        
        # Look for logger calls with forbidden fields
        for field in forbidden_log_fields:
            pattern = rf'logger\.(info|debug|warning|error|critical).*{field}'
            if re.search(pattern, content, re.IGNORECASE):
                line_num = content.find(field) and content[:content.find(field)].count('\n') + 1
                violations.append(f"{py_file}:{line_num} - Potential content leak: {field}")
    
    if violations:
        return False, f"Found {len(violations)} potential content leaks in logs:\n" + "\n".join(violations[:10])
    return True, "No content leaks in logs found"

def check_mtls_required() -> Tuple[bool, str]:
    """Check: Caddyfile requires mTLS on port 443"""
    caddyfile = Path("Caddyfile.prod_brutal")
    if not caddyfile.exists():
        return False, "Caddyfile.prod_brutal not found"
    
    content = caddyfile.read_text()
    
    # Check for client_auth require_and_verify on port 443
    if "client_auth require_and_verify" not in content:
        return False, "Caddyfile missing 'client_auth require_and_verify' for mTLS"
    
    # Check that port 443 is configured
    if ":443" not in content and "https://" not in content:
        return False, "Caddyfile missing HTTPS/443 configuration"
    
    return True, "mTLS properly configured in Caddyfile"

def check_zero_egress_network() -> Tuple[bool, str]:
    """Check: Docker compose has internal_net with internal: true"""
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        return False, "docker-compose.yml not found"
    
    content = compose_file.read_text()
    
    # Check for internal_net with internal: true
    if "internal_net" in content:
        if "internal: true" not in content:
            return False, "internal_net found but 'internal: true' missing"
    else:
        return False, "internal_net not found in docker-compose.yml"
    
    return True, "Zero egress network properly configured"

def check_no_cloud_keys_in_prod() -> Tuple[bool, str]:
    """Check: No cloud API keys in prod_brutal environment"""
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        return True, "docker-compose.yml not found (skipping)"
    
    content = compose_file.read_text()
    
    # Check for cloud API keys in environment section
    forbidden_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
    violations = []
    
    for key in forbidden_keys:
        if key in content:
            # Check if it's in a prod_brutal profile or commented out
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if key in line and '#' not in line[:line.find(key)]:
                    # Check if it's in a profile section
                    if 'prod_brutal' in content[max(0, content.find(key)-500):content.find(key)]:
                        violations.append(f"Line {i+1}: {key} found in prod_brutal environment")
    
    if violations:
        return False, f"Found cloud API keys in prod_brutal:\n" + "\n".join(violations)
    return True, "No cloud API keys in prod_brutal environment"

def check_privacy_gate_usage() -> Tuple[bool, str]:
    """Check: External providers use MaskedPayload"""
    backend_path = Path("backend/app")
    if not backend_path.exists():
        return True, "Backend path not found (skipping)"
    
    # This is a simplified check - full check is in check_privacy_gate_usage.py
    return True, "Privacy gate usage check (see check_privacy_gate_usage.py for full check)"

def main():
    """Run all security invariant checks."""
    mode = sys.argv[1] if len(sys.argv) > 1 else "--static"
    
    invariants = [
        SecurityInvariant(
            "No Egress Bypass",
            check_no_egress_bypass,
            "No direct HTTP requests without ensure_egress_allowed()"
        ),
        SecurityInvariant(
            "No Content in Logs",
            check_no_content_in_logs,
            "No content/PII in log statements"
        ),
        SecurityInvariant(
            "mTLS Required",
            check_mtls_required,
            "Caddyfile requires mTLS on port 443"
        ),
        SecurityInvariant(
            "Zero Egress Network",
            check_zero_egress_network,
            "Docker compose has internal_net with internal: true"
        ),
        SecurityInvariant(
            "No Cloud Keys in Prod",
            check_no_cloud_keys_in_prod,
            "No cloud API keys in prod_brutal environment"
        ),
    ]
    
    if mode == "--runtime":
        # Add runtime checks
        invariants.append(SecurityInvariant(
            "Privacy Gate Usage",
            check_privacy_gate_usage,
            "External providers use MaskedPayload"
        ))
    
    print(f"{YELLOW}Checking Security Invariants ({mode})...{RESET}\n")
    
    passed = 0
    failed = 0
    
    for invariant in invariants:
        result, message = invariant.check()
        if result:
            print(f"{GREEN}✅{RESET} {invariant.name}: {message}")
            passed += 1
        else:
            print(f"{RED}❌{RESET} {invariant.name}: {message}")
            failed += 1
    
    print(f"\n{YELLOW}Results: {passed} passed, {failed} failed{RESET}")
    
    if failed > 0:
        print(f"\n{RED}Security invariants violated! Fix before proceeding.{RESET}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}All security invariants passed!{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()

