#!/usr/bin/env bash
set -euo pipefail

# Verify README examples work
# Usage: ./scripts/verify_docs.sh

BACKEND_PORT=${BACKEND_PORT:-8000}
API="http://localhost:${BACKEND_PORT}/health"

echo "🔍 Verifying documentation examples..."

# Test health endpoint
RES=$(curl -s "$API" || echo "FAIL")
if echo "$RES" | grep -qi '"status".*"ok"'; then
    echo "✅ Health check OK"
else
    echo "❌ Health check failed"
    exit 1
fi

echo "✅ Documentation verification complete"

