#!/bin/bash
# Verify mTLS configuration
# Tests: 403 without cert, 200 with cert

set -e

PROXY_URL="${PROXY_URL:-https://localhost}"
# Health endpoint is available via HTTP (port 80) without mTLS
# For mTLS test, we use HTTPS which requires cert
HEALTH_URL_HTTP="http://localhost/health"
HEALTH_URL_HTTPS="${PROXY_URL}/health"
CA_CERT="certs/ca.crt"
CLIENT_CERT="certs/client.crt"
CLIENT_KEY="certs/client.key"

echo "Verifying mTLS configuration..."
echo ""

# Test 1: Request to /api/* without client certificate (should fail)
# Note: /health is available via HTTP without mTLS, but /api/* requires mTLS
echo "Test 1: Request WITHOUT client certificate (should fail with 403)..."
API_URL="${PROXY_URL}/api/v1/projects"
# Try curl with timeout - if it fails (no cert), that's expected
HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" --max-time 5 "${API_URL}" 2>/dev/null || echo "000")
# Extract just the HTTP code (remove any error text)
HTTP_CODE=$(echo "${HTTP_CODE}" | grep -oE '[0-9]{3}' | head -1 || echo "000")
if [ "${HTTP_CODE}" = "403" ]; then
    echo "✅ PASS: Request without cert correctly blocked (403)"
elif [ "${HTTP_CODE}" = "400" ]; then
    echo "✅ PASS: Request without cert correctly blocked (400 - TLS handshake failed)"
elif [ "${HTTP_CODE}" = "000" ] || [ -z "${HTTP_CODE}" ]; then
    echo "✅ PASS: Request without cert correctly blocked (connection failed - TLS handshake failed)"
else
    echo "❌ FAIL: Expected 403/400/000, got ${HTTP_CODE}"
    exit 1
fi

echo ""

# Test 2: Request with client certificate (should succeed)
if [ ! -f "${CLIENT_CERT}" ] || [ ! -f "${CLIENT_KEY}" ] || [ ! -f "${CA_CERT}" ]; then
    echo "⚠️  WARN: Client certificates not found (${CLIENT_CERT}, ${CLIENT_KEY}, ${CA_CERT})"
    echo "   Run scripts/generate_certs.sh first"
    exit 1
fi

echo "Test 2: Request WITH client certificate (should succeed with 200)..."
HTTP_CODE=$(curl -k --cert "${CLIENT_CERT}" --key "${CLIENT_KEY}" --cacert "${CA_CERT}" \
    -s -o /dev/null -w "%{http_code}" "${HEALTH_URL_HTTPS}")

if [ "${HTTP_CODE}" = "200" ]; then
    echo "✅ PASS: Request with cert succeeded (200)"
else
    echo "❌ FAIL: Expected 200, got ${HTTP_CODE}"
    exit 1
fi

echo ""
echo "✅ mTLS verification complete!"
