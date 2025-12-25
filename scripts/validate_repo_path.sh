#!/bin/bash
# Validate repository path is safe for Docker
# Checks for colon in path and verifies Docker can mount

set -e

CURRENT_PATH=$(pwd)

echo "Validating repository path..."
echo "Current path: ${CURRENT_PATH}"
echo ""

# Check for colon
if [[ "$CURRENT_PATH" == *":"* ]]; then
    echo "❌ FAIL: Path contains ':'"
    echo "   This breaks Docker bind mounts"
    echo "   Fix: Rename repository folder to remove ':'"
    echo "   See: docs/REPO_PATH_FIX.md"
    exit 1
fi

echo "✅ Path does not contain colon"

# Check Docker can access path
if ! docker info &>/dev/null; then
    echo "⚠️  WARNING: Docker not running (cannot test mounts)"
    echo "   Start Docker Desktop and run this script again"
else
    # Test Docker can read path
    echo "Testing Docker mount..."
    if docker run --rm -v "${CURRENT_PATH}:/test:ro" alpine ls /test &>/dev/null; then
        echo "✅ Docker can mount path"
    else
        echo "❌ FAIL: Docker cannot mount path"
        exit 1
    fi
fi

# Check Makefile exists
if [ ! -f "Makefile" ]; then
    echo "❌ FAIL: Makefile not found"
    exit 1
fi

echo "✅ Makefile exists"

echo ""
echo "✅ Path validation passed - Ready for verification"

