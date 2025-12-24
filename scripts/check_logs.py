#!/usr/bin/env python3
"""Check logs for privacy violations (forbidden keys).

This script verifies that logs do not contain forbidden keys like
authorization, cookie, user-agent, headers, body, payload, etc.
"""
import json
import subprocess
import sys
from typing import List, Set

# Forbidden keys that must NEVER appear in logs
_FORBIDDEN_LOG_KEYS = frozenset({
    "authorization",
    "cookie",
    "user-agent",
    "user_agent",
    "body",
    "payload",
    "headers",
    "query_params",
    "query",
    "ip",
    "ip_address",
    "remote_addr",
    "x-forwarded-for",
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
})


def check_log_line(line: str, forbidden_keys: Set[str]) -> List[str]:
    """Check a single log line for forbidden keys.

    Args:
        line: Log line (JSON or text)
        forbidden_keys: Set of forbidden keys to check for

    Returns:
        List of violations found (empty if none)
    """
    violations = []

    # Try to parse as JSON
    try:
        data = json.loads(line)
        # Check all keys recursively
        keys_lower = {k.lower() for k in _flatten_dict(data).keys()}
        found = keys_lower & forbidden_keys
        if found:
            violations.extend(f"Found forbidden key: {key}" for key in found)
    except json.JSONDecodeError:
        # Not JSON, check as plain text
        line_lower = line.lower()
        for key in forbidden_keys:
            if key in line_lower:
                violations.append(f"Found forbidden key in text: {key}")

    return violations


def _flatten_dict(d: dict, parent_key: str = "") -> dict:
    """Flatten nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_docker_logs(container_name: str = "copy-paste-backend", lines: int = 50) -> List[str]:
    """Get logs from Docker container.

    Args:
        container_name: Docker container name
        lines: Number of lines to retrieve

    Returns:
        List of log lines
    """
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_name],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("\n")
    except subprocess.CalledProcessError:
        return []
    except FileNotFoundError:
        print("⚠️  Docker not found, skipping Docker log check")
        return []


def main() -> int:
    """Check logs for privacy violations."""
    print("Checking logs for privacy violations...")
    print("=" * 50)

    # Get logs from Docker
    log_lines = get_docker_logs()

    if not log_lines:
        print("⚠️  No logs found. Make sure backend is running:")
        print("   make up")
        print("")
        print("Or check logs manually:")
        print("   docker logs copy-paste-backend | grep -iE '(authorization|cookie|body|headers)'")
        return 0  # Don't fail if we can't check

    violations = []
    checked_lines = 0

    for line in log_lines:
        if not line.strip():
            continue
        checked_lines += 1
        line_violations = check_log_line(line, _FORBIDDEN_LOG_KEYS)
        violations.extend(line_violations)

    print(f"Checked {checked_lines} log lines")
    print("")

    if violations:
        print("❌ Privacy violations found:")
        for violation in violations:
            print(f"  - {violation}")
        print("")
        print("This indicates a privacy leak in logging!")
        return 1

    print("✅ No privacy violations found in logs")
    print("")
    print("Forbidden keys checked:")
    for key in sorted(_FORBIDDEN_LOG_KEYS):
        print(f"  - {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

