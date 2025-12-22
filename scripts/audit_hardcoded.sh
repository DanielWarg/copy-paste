#!/usr/bin/env bash
set -euo pipefail

# Audit for hardcoded URLs, tokens, secrets
# Usage: ./scripts/audit_hardcoded.sh

echo "🔍 Auditing for hardcoded values..."

fail=0

# Check for hardcoded URLs
if grep -RIn --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git \
    -E '(http://|https://).*(localhost|api\.example|hardcoded)' .; then
    echo "⚠️  Warning: Hardcoded URL found"
    fail=1
fi

# Check for hardcoded secrets
if grep -RIn --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git \
    -E '(SECRET|API_KEY|TOKEN|PASSWORD)=[A-Za-z0-9]{10,}' .; then
    echo "⚠️  Warning: Possible secret in code"
    fail=1
fi

if [ $fail -eq 0 ]; then
    echo "✅ No hardcoded values found"
else
    echo "❌ Hardcoded values found - please review"
    exit 1
fi

