#!/bin/bash
# Verify Frontend Exposure via Proxy (Phase B)
# Tests mTLS enforcement, security headers, and endpoint separation

set -e

CERT_DIR="certs"
CLIENT_CERT="${CERT_DIR}/client.crt"
CLIENT_KEY="${CERT_DIR}/client.key"
CA_CERT="${CERT_DIR}/ca.crt"

echo "════════════════════════════════════════════════════════════"
echo "Phase B - Frontend Exposure Verification"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if certificates exist
if [ ! -f "${CLIENT_CERT}" ] || [ ! -f "${CLIENT_KEY}" ] || [ ! -f "${CA_CERT}" ]; then
    echo "❌ ERROR: Certificates not found. Run ./scripts/generate_certs.sh first"
    exit 1
fi

# Check if services are running
if ! docker ps | grep -q "copy-paste-proxy-brutal"; then
    echo "❌ ERROR: Proxy container not running"
    echo "   Start with: docker-compose -f docker-compose.prod_brutal.yml up -d"
    exit 1
fi

if ! docker ps | grep -q "copy-paste-backend-brutal"; then
    echo "❌ ERROR: Backend container not running"
    echo "   Start with: docker-compose -f docker-compose.prod_brutal.yml up -d"
    exit 1
fi

echo "Waiting for services to be ready..."
sleep 5

FAILED=0

# Test 1: /ui/* without cert -> 403
echo ""
echo "Test 1: /ui/* without cert (should be 403)..."
RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/ui/ 2>&1 || echo "000")
if [ "$RESPONSE" = "403" ]; then
    echo "   ✅ PASS: /ui/* requires mTLS (403 without cert)"
else
    echo "   ❌ FAIL: /ui/* returned $RESPONSE (expected 403)"
    FAILED=1
fi

# Test 2: /api/* without cert -> 403
echo ""
echo "Test 2: /api/* without cert (should be 403)..."
RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/api/v1/projects 2>&1 || echo "000")
if [ "$RESPONSE" = "403" ]; then
    echo "   ✅ PASS: /api/* requires mTLS (403 without cert)"
else
    echo "   ❌ FAIL: /api/* returned $RESPONSE (expected 403)"
    FAILED=1
fi

# Test 3: /health without cert -> 200
echo ""
echo "Test 3: /health without cert (should be 200)..."
RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/health 2>&1 || echo "000")
if [ "$RESPONSE" = "200" ]; then
    echo "   ✅ PASS: /health accessible without cert (200)"
else
    echo "   ❌ FAIL: /health returned $RESPONSE (expected 200)"
    FAILED=1
fi

# Test 4: /ready without cert -> 200 or 503 (both acceptable)
echo ""
echo "Test 4: /ready without cert (should be 200 or 503)..."
RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/ready 2>&1 || echo "000")
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "503" ]; then
    echo "   ✅ PASS: /ready accessible without cert ($RESPONSE)"
else
    echo "   ❌ FAIL: /ready returned $RESPONSE (expected 200 or 503)"
    FAILED=1
fi

# Test 5: /ui/* with cert -> 200
echo ""
echo "Test 5: /ui/* with cert (should be 200)..."
RESPONSE=$(curl -k --cert "${CLIENT_CERT}" --key "${CLIENT_KEY}" --cacert "${CA_CERT}" \
    -s -o /dev/null -w "%{http_code}" https://localhost/ui/ 2>&1 || echo "000")
if [ "$RESPONSE" = "200" ]; then
    echo "   ✅ PASS: /ui/* accessible with cert (200)"
else
    echo "   ❌ FAIL: /ui/* returned $RESPONSE (expected 200)"
    FAILED=1
fi

# Test 6: /api/* with cert -> 200
echo ""
echo "Test 6: /api/* with cert (should be 200)..."
RESPONSE=$(curl -k --cert "${CLIENT_CERT}" --key "${CLIENT_KEY}" --cacert "${CA_CERT}" \
    -s -o /dev/null -w "%{http_code}" https://localhost/api/v1/projects 2>&1 || echo "000")
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "404" ]; then
    # 200 = success, 404 = endpoint not found (but mTLS worked)
    echo "   ✅ PASS: /api/* accessible with cert ($RESPONSE)"
else
    echo "   ❌ FAIL: /api/* returned $RESPONSE (expected 200 or 404)"
    FAILED=1
fi

# Test 7: Security headers on /ui/*
echo ""
echo "Test 7: Security headers on /ui/*..."
HEADERS=$(curl -k --cert "${CLIENT_CERT}" --key "${CLIENT_KEY}" --cacert "${CA_CERT}" \
    -s -I https://localhost/ui/ 2>&1)

MISSING_HEADERS=0

if ! echo "$HEADERS" | grep -qi "X-Content-Type-Options.*nosniff"; then
    echo "   ❌ FAIL: Missing X-Content-Type-Options: nosniff"
    MISSING_HEADERS=1
fi

if ! echo "$HEADERS" | grep -qi "X-Frame-Options.*DENY"; then
    echo "   ❌ FAIL: Missing X-Frame-Options: DENY"
    MISSING_HEADERS=1
fi

if ! echo "$HEADERS" | grep -qi "Referrer-Policy.*no-referrer"; then
    echo "   ❌ FAIL: Missing Referrer-Policy: no-referrer"
    MISSING_HEADERS=1
fi

if ! echo "$HEADERS" | grep -qi "Cache-Control.*no-store"; then
    echo "   ❌ FAIL: Missing Cache-Control: no-store"
    MISSING_HEADERS=1
fi

if [ $MISSING_HEADERS -eq 0 ]; then
    echo "   ✅ PASS: All required security headers present on /ui/*"
else
    FAILED=1
fi

# Test 8: Security headers on /api/*
echo ""
echo "Test 8: Security headers on /api/*..."
HEADERS=$(curl -k --cert "${CLIENT_CERT}" --key "${CLIENT_KEY}" --cacert "${CA_CERT}" \
    -s -I https://localhost/api/v1/projects 2>&1)

MISSING_HEADERS=0

if ! echo "$HEADERS" | grep -qi "X-Content-Type-Options.*nosniff"; then
    echo "   ❌ FAIL: Missing X-Content-Type-Options: nosniff"
    MISSING_HEADERS=1
fi

if ! echo "$HEADERS" | grep -qi "X-Frame-Options.*DENY"; then
    echo "   ❌ FAIL: Missing X-Frame-Options: DENY"
    MISSING_HEADERS=1
fi

if [ $MISSING_HEADERS -eq 0 ]; then
    echo "   ✅ PASS: All required security headers present on /api/*"
else
    FAILED=1
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo "✅ Frontend Exposure Verification: PASS"
    echo "════════════════════════════════════════════════════════════"
    exit 0
else
    echo "❌ Frontend Exposure Verification: FAIL"
    echo "════════════════════════════════════════════════════════════"
    exit 1
fi

