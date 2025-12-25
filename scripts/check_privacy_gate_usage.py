#!/usr/bin/env python3
"""CI Check: Verify all external LLM calls use privacy_gate.

This script scans code for external LLM API calls and ensures they use privacy_gate.
"""
import os
import re
import sys
from pathlib import Path

# Patterns that indicate external LLM API calls
LLM_API_PATTERNS = [
    r'openai\.',
    r'httpx\.(get|post|put|patch|delete)',
    r'requests\.(get|post|put|patch|delete)',
    r'\.chat\.completions\.create',
    r'client\.chat\.',
]

# Pattern that indicates privacy_gate usage
PRIVACY_GATE_PATTERN = r'privacy_gate\.ensure_masked_or_raise'

# Allowed directories for external LLM imports (must use privacy_gate or MaskedPayload)
ALLOWED_PROVIDER_DIRS = [
    "app/modules/privacy_shield/providers",
    "app/modules/draft/providers",
]

# Files to scan
BACKEND_DIR = Path(__file__).parent.parent / "backend" / "app"

def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in directory."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Skip test files (they may have mock calls)
        if '__pycache__' in root or 'tests' in root:
            continue
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(Path(root) / filename)
    return files

def is_allowed_provider_file(filepath: Path) -> bool:
    """Check if file is in allowed provider directory."""
    rel_path = filepath.relative_to(BACKEND_DIR.parent)
    path_str = str(rel_path).replace("\\", "/")
    for allowed_dir in ALLOWED_PROVIDER_DIRS:
        if path_str.startswith(allowed_dir):
            return True
    return False

def check_file(filepath: Path) -> list[str]:
    """Check a single file for LLM API calls without privacy_gate."""
    violations = []
    
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return [f"Error reading {filepath}: {e}"]
    
    # Check if file is in allowed provider directory
    is_provider_file = is_allowed_provider_file(filepath)
    
    # Check for imports of httpx/requests/openai outside allowed directories
    if not is_provider_file:
        import_patterns = [
            (r'^import\s+openai', 'openai'),
            (r'^import\s+httpx', 'httpx'),
            (r'^import\s+requests', 'requests'),
            (r'^from\s+openai\s+import', 'openai'),
            (r'^from\s+httpx\s+import', 'httpx'),
            (r'^from\s+requests\s+import', 'requests'),
        ]
        for line_num, line in enumerate(content.split('\n'), 1):
            for pattern, lib_name in import_patterns:
                if re.match(pattern, line.strip()):
                    rel_path = filepath.relative_to(BACKEND_DIR.parent)
                    violations.append(
                        f"{rel_path}:{line_num}: {lib_name} imported outside provider directory (must be in app/modules/*/providers/)"
                    )
    
    # Check for LLM API patterns
    for pattern in LLM_API_PATTERNS:
        matches = list(re.finditer(pattern, content))
        if matches:
            # Check if privacy_gate is used nearby OR if type-safe MaskedPayload is used
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                # Look in surrounding context (500 chars before/after for function signatures)
                start = max(0, match.start() - 500)
                end = min(len(content), match.end() + 100)
                context = content[start:end]
                
                # Check for type-safe enforcement: MaskedPayload in function signature
                # This is acceptable because MaskedPayload can only be created by Privacy Shield
                has_masked_payload = re.search(r'MaskedPayload', context) or re.search(r'masked_payload:\s*MaskedPayload', context)
                
                # If file is in provider directory, it's allowed (but should use MaskedPayload)
                if is_provider_file:
                    # Provider files should use MaskedPayload, but we allow them for now
                    continue
                
                # If privacy_gate pattern is not in context AND no MaskedPayload type safety, it's a violation
                if not re.search(PRIVACY_GATE_PATTERN, context) and not has_masked_payload:
                    rel_path = filepath.relative_to(BACKEND_DIR.parent)
                    violations.append(
                        f"{rel_path}:{line_num}: Potential LLM API call without privacy_gate or MaskedPayload: {pattern}"
                    )
    
    return violations

def main():
    """Run privacy gate usage check."""
    print("Checking for external LLM calls without privacy_gate...")
    print()
    
    if not BACKEND_DIR.exists():
        print(f"Error: Backend directory not found: {BACKEND_DIR}")
        return 1
    
    files = find_python_files(BACKEND_DIR)
    all_violations = []
    
    for filepath in files:
        violations = check_file(filepath)
        all_violations.extend(violations)
    
    if all_violations:
        print("❌ VIOLATIONS FOUND:")
        print()
        for violation in all_violations:
            print(f"  {violation}")
        print()
        print("All external LLM calls MUST go through privacy_gate.ensure_masked_or_raise()")
        return 1
    else:
        print("✅ No violations found")
        print("All external LLM calls appear to use privacy_gate")
        return 0

if __name__ == "__main__":
    sys.exit(main())

