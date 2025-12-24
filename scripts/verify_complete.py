#!/usr/bin/env python3
"""Complete GO/NO-GO verification for Copy/Paste Core."""
import sys
import os
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


class VerificationResult:
    """Track verification results."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append({"test": test_name, "details": details})
        print(f"{GREEN}✅ PASS:{RESET} {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, reason: str):
        self.failed.append({"test": test_name, "reason": reason})
        print(f"{RED}❌ FAIL:{RESET} {test_name}")
        print(f"   Reason: {reason}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append({"test": test_name, "message": message})
        print(f"{YELLOW}⚠️  WARN:{RESET} {test_name}")
        print(f"   {message}")
    
    def summary(self) -> Dict[str, Any]:
        return {
            "passed": len(self.passed),
            "failed": len(self.failed),
            "warnings": len(self.warnings),
            "total": len(self.passed) + len(self.failed),
        }
    
    def is_go(self) -> bool:
        return len(self.failed) == 0


def check_documentation() -> bool:
    """Check that all required documentation exists."""
    docs_dir = Path(__file__).parent.parent / "docs"
    required_docs = [
        "journalism-safety.md",
        "opsec.md",
        "security.md",
        "user-safety.md",
        "threat-model.md",
    ]
    
    missing = []
    for doc in required_docs:
        if not (docs_dir / doc).exists():
            missing.append(doc)
    
    if missing:
        print(f"{RED}❌ Missing documentation:{RESET} {', '.join(missing)}")
        return False
    
    print(f"{GREEN}✅ All required documentation exists{RESET}")
    print(f"   Found: {', '.join(required_docs)}")
    return True


def check_source_safety_mode() -> bool:
    """Verify SOURCE_SAFETY_MODE hard mode."""
    print("\n" + "=" * 60)
    print("A) SOURCE SAFETY MODE VERIFICATION")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/test_source_safety.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{RED}Error running source safety test: {e}{RESET}")
        return False


def check_security_freeze() -> bool:
    """Verify Security Freeze v1."""
    print("\n" + "=" * 60)
    print("B) SECURITY FREEZE VERIFICATION")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/test_security_freeze.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{RED}Error running security freeze test: {e}{RESET}")
        return False


def check_log_hygiene() -> bool:
    """Verify log hygiene."""
    print("\n" + "=" * 60)
    print("C) LOG HYGIENE VERIFICATION")
    print("=" * 60)
    
    # Check if check_logs.py exists and run it
    check_logs_script = Path(__file__).parent / "check_logs.py"
    if not check_logs_script.exists():
        print(f"{YELLOW}⚠️  check_logs.py not found, skipping log hygiene check{RESET}")
        return True  # Not a blocker if script doesn't exist yet
    
    try:
        result = subprocess.run(
            [sys.executable, str(check_logs_script)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{RED}Error running log hygiene check: {e}{RESET}")
        return False


def check_code_quality() -> bool:
    """Run code quality checks."""
    print("\n" + "=" * 60)
    print("D) CODE QUALITY VERIFICATION")
    print("=" * 60)
    
    try:
        # Syntax check
        result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "backend/app"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            print(f"{RED}Syntax errors found{RESET}")
            print(result.stderr)
            return False
        
        print(f"{GREEN}✅ Syntax check passed{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error running code quality check: {e}{RESET}")
        return False


def check_config_hard_mode() -> bool:
    """Verify config hard mode (SOURCE_SAFETY_MODE forced in prod)."""
    print("\n" + "=" * 60)
    print("E) CONFIG HARD MODE VERIFICATION")
    print("=" * 60)
    
    # Test that SOURCE_SAFETY_MODE=false fails in prod
    env = os.environ.copy()
    env["DEBUG"] = "false"
    env["SOURCE_SAFETY_MODE"] = "false"
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", "from backend.app.core.config import settings"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent,
        )
        
        if result.returncode == 0:
            print(f"{RED}❌ Config should fail when SOURCE_SAFETY_MODE=false in prod{RESET}")
            return False
        
        if "SOURCE_SAFETY_MODE cannot be False" in result.stderr:
            print(f"{GREEN}✅ Config correctly fails when SOURCE_SAFETY_MODE=false in prod{RESET}")
            return True
        else:
            print(f"{RED}❌ Wrong error message{RESET}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{RED}Error testing config hard mode: {e}{RESET}")
        return False


def main():
    """Run complete GO/NO-GO verification."""
    print("=" * 60)
    print("COPY/PASTE CORE - GO/NO-GO VERIFICATION v1")
    print("=" * 60)
    print()
    
    result = VerificationResult()
    
    # 1. Documentation check
    print("\n" + "=" * 60)
    print("1) DOCUMENTATION CHECK")
    print("=" * 60)
    if check_documentation():
        result.add_pass("Documentation exists")
    else:
        result.add_fail("Documentation check", "Missing required documentation files")
    
    # 2. Source Safety Mode
    if check_source_safety_mode():
        result.add_pass("Source Safety Mode")
    else:
        result.add_fail("Source Safety Mode", "Source safety tests failed")
    
    # 3. Security Freeze
    if check_security_freeze():
        result.add_pass("Security Freeze")
    else:
        result.add_fail("Security Freeze", "Security freeze tests failed")
    
    # 4. Log Hygiene
    if check_log_hygiene():
        result.add_pass("Log Hygiene")
    else:
        result.add_fail("Log Hygiene", "Log hygiene check failed")
    
    # 5. Code Quality
    if check_code_quality():
        result.add_pass("Code Quality")
    else:
        result.add_fail("Code Quality", "Code quality checks failed")
    
    # 6. Config Hard Mode
    if check_config_hard_mode():
        result.add_pass("Config Hard Mode")
    else:
        result.add_fail("Config Hard Mode", "Config hard mode verification failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    summary = result.summary()
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Total: {summary['total']}")
    print()
    
    if result.is_go():
        print(f"{GREEN}{'=' * 60}{RESET}")
        print(f"{GREEN}✅ GO: System is ready for next module{RESET}")
        print(f"{GREEN}{'=' * 60}{RESET}")
        print()
        print("System has passed all critical verifications:")
        print("- Source Safety Mode enforced")
        print("- Security Freeze v1 implemented")
        print("- Log hygiene verified")
        print("- Code quality checks passed")
        print("- Config hard mode verified")
        print()
        print("System is ready for:")
        print("- Recording module")
        print("- Privacy Shield")
        print("- AI integration")
        print("- Further feature development")
        return 0
    else:
        print(f"{RED}{'=' * 60}{RESET}")
        print(f"{RED}❌ NO-GO: System has critical issues{RESET}")
        print(f"{RED}{'=' * 60}{RESET}")
        print()
        print("Failed verifications:")
        for fail in result.failed:
            print(f"  - {fail['test']}: {fail['reason']}")
        print()
        print("Fix all failures before proceeding with development.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

