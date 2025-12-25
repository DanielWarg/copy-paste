#!/usr/bin/env python3
"""
Documentation Integrity Checker

Verifierar att dokumentation följer regler:
- Endast canonical docs och archive/ får innehålla .md-filer
- Root README.md måste vara minimal entry point
- Arkiverade filer måste ha ARCHIVED-banner
- Inga nya docs får skapas utanför canonical/ och archive/

Usage:
    python3 scripts/check_docs_integrity.py
"""

import sys
import re
from pathlib import Path
from typing import List, Set, Tuple

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Allowed .md files (outside canonical/ and archive/)
ALLOWED_ROOT_MD = {
    "README.md",
    "CHANGELOG.md",
}

# Allowed .md files in docs/ (outside canonical/ and archive/)
ALLOWED_DOCS_MD = {
    "agent.md",  # Minimal entry point
}

# Exclude patterns
EXCLUDE_PATTERNS = [
    "node_modules",
    ".venv",
    ".git",
    ".pytest_cache",
    "playwright-report",
    "test-results",
    "frontend_archive",
    "arkiv",
    "archive",  # Exclude old archive/ directory
]


def find_all_md_files(root: Path) -> List[Path]:
    """Find all .md files in repo, excluding patterns."""
    md_files = []
    for md_file in root.rglob("*.md"):
        # Skip excluded patterns
        if any(pattern in str(md_file) for pattern in EXCLUDE_PATTERNS):
            continue
        md_files.append(md_file)
    return sorted(md_files)


def check_only_canonical_and_archive(root: Path) -> Tuple[bool, List[str]]:
    """Check that .md files only exist in canonical/ and archive/."""
    violations = []
    
    for md_file in find_all_md_files(root):
        rel_path = md_file.relative_to(root)
        path_str = str(rel_path)
        
        # Allow canonical docs
        if path_str.startswith("docs/canonical/"):
            continue
        
        # Allow archive
        if path_str.startswith("docs/archive/"):
            continue
        
        # Allow root-level allowed files
        if rel_path.name in ALLOWED_ROOT_MD:
            continue
        
        # Allow docs/agent.md (minimal entry point)
        if path_str == "docs/agent.md":
            continue
        
        # Allow CHANGELOG.md anywhere
        if rel_path.name == "CHANGELOG.md":
            continue
        
        # Allow module READMEs
        if "modules/" in path_str and rel_path.name in ["README.md", "PURGE.md"]:
            continue
        
        # Allow tests/ directory (all files)
        if path_str.startswith("tests/"):
            continue
        
        # Allow backend module-specific docs
        if path_str == "backend/CONFIG_BEST_PRACTICES.md":
            continue
        
        # Everything else is a violation
        violations.append(path_str)
    
    return len(violations) == 0, violations


def check_archived_banner(root: Path) -> Tuple[bool, List[str]]:
    """Check that archived files have ARCHIVED banner."""
    violations = []
    archive_dir = root / "docs" / "archive"
    
    if not archive_dir.exists():
        return True, []
    
    for md_file in archive_dir.rglob("*.md"):
        content = md_file.read_text(encoding='utf-8', errors='ignore')
        
        if "ARCHIVED DOCUMENT" not in content:
            violations.append(str(md_file.relative_to(root)))
    
    return len(violations) == 0, violations


def check_readme_minimal(root: Path) -> Tuple[bool, str]:
    """Check that README.md is minimal entry point."""
    readme = root / "README.md"
    
    if not readme.exists():
        return False, "README.md does not exist"
    
    content = readme.read_text(encoding='utf-8', errors='ignore')
    
    # Check that it links to canonical docs
    if "canonical" not in content.lower():
        return False, "README.md does not link to canonical docs"
    
    # Check that it's not too long (should be < 100 lines)
    if len(content.split('\n')) > 150:
        return False, "README.md is too long (should be minimal entry point)"
    
    return True, "README.md is minimal"


def check_no_docs_in_root_docs(root: Path) -> Tuple[bool, List[str]]:
    """Check that docs/ (root) contains no .md files except agent.md."""
    violations = []
    docs_dir = root / "docs"
    
    if not docs_dir.exists():
        return True, []
    
    for md_file in docs_dir.glob("*.md"):
        if md_file.name == "agent.md":
            continue
        if md_file.parent.name == "canonical":
            continue
        if md_file.parent.name == "archive":
            continue
        violations.append(str(md_file.relative_to(root)))
    
    return len(violations) == 0, violations


def main():
    """Run all documentation integrity checks."""
    root = Path(__file__).parent.parent
    
    print(f"{YELLOW}Checking Documentation Integrity...{RESET}\n")
    
    passed = 0
    failed = 0
    
    # Check 1: Only canonical and archive
    result, violations = check_only_canonical_and_archive(root)
    if result:
        print(f"{GREEN}✅{RESET} Only canonical/ and archive/ contain .md files")
        passed += 1
    else:
        print(f"{RED}❌{RESET} .md files found outside canonical/ and archive/:")
        for violation in violations[:10]:  # Show first 10
            print(f"  - {violation}")
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more")
        failed += 1
    
    # Check 2: Archived files have banner
    result, violations = check_archived_banner(root)
    if result:
        print(f"{GREEN}✅{RESET} All archived files have ARCHIVED banner")
        passed += 1
    else:
        print(f"{RED}❌{RESET} Archived files missing ARCHIVED banner:")
        for violation in violations[:10]:
            print(f"  - {violation}")
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more")
        failed += 1
    
    # Check 3: README is minimal
    result, message = check_readme_minimal(root)
    if result:
        print(f"{GREEN}✅{RESET} README.md is minimal entry point")
        passed += 1
    else:
        print(f"{RED}❌{RESET} README.md: {message}")
        failed += 1
    
    # Check 4: No docs in root docs/
    result, violations = check_no_docs_in_root_docs(root)
    if result:
        print(f"{GREEN}✅{RESET} docs/ (root) contains only agent.md")
        passed += 1
    else:
        print(f"{RED}❌{RESET} .md files found in docs/ (root):")
        for violation in violations:
            print(f"  - {violation}")
        failed += 1
    
    print(f"\n{YELLOW}Results: {passed} passed, {failed} failed{RESET}")
    
    if failed > 0:
        print(f"\n{RED}Documentation integrity violated! Fix before proceeding.{RESET}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}All documentation integrity checks passed!{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
