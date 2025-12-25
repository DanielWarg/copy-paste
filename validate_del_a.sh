#!/bin/bash
# Snabb validering DEL A - Network Bunker (ingen docker-compose config)

echo "════════════════════════════════════════════════════════════"
echo "DEL A VALIDATION - Network Bunker"
echo "════════════════════════════════════════════════════════════"
echo ""

FAILED=0

# Test 1: Files exist
echo "[1/6] Checking required files..."
FILES=("docker-compose.prod_brutal.yml" "Caddyfile.prod_brutal" "scripts/generate_certs.sh" "scripts/verify_mtls.sh")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file MISSING"
        FAILED=1
    fi
done

# Test 2: Backend has no ports in docker-compose file
echo ""
echo "[2/6] Checking backend has no ports (robust section scan)..."
# Extract backend section and check for ports: keyword
BACKEND_SECTION=$(awk '/^  backend:/,/^  [a-z]/' docker-compose.prod_brutal.yml | head -50)
if echo "$BACKEND_SECTION" | grep -q "^[[:space:]]*ports:"; then
    echo "   ❌ FAIL - Backend section contains 'ports:'"
    echo "$BACKEND_SECTION" | grep -A 3 "^[[:space:]]*ports:"
    FAILED=1
else
    echo "   ✅ PASS - Backend section has NO 'ports:' keyword"
fi

# Test 3: Internal network configured
echo ""
echo "[3/6] Checking internal network configuration..."
if grep -q "internal: true" docker-compose.prod_brutal.yml; then
    echo "   ✅ PASS - internal_net with internal: true"
    # Verify backend is ONLY on internal_net
    BACKEND_NETWORKS=$(awk '/^  backend:/,/^  [a-z]/' docker-compose.prod_brutal.yml | grep -A 5 "networks:" | grep -E "internal_net|default" | head -5)
    if echo "$BACKEND_NETWORKS" | grep -q "default"; then
        echo "   ⚠️  WARN - Backend also on 'default' network (may have internet access)"
    else
        echo "   ✅ PASS - Backend only on internal_net"
    fi
else
    echo "   ❌ FAIL - internal network not found"
    FAILED=1
fi

# Test 4: Scripts syntax
echo ""
echo "[4/6] Validating script syntax..."
if bash -n scripts/generate_certs.sh 2>&1; then
    echo "   ✅ generate_certs.sh"
else
    echo "   ❌ generate_certs.sh has errors"
    FAILED=1
fi

if bash -n scripts/verify_mtls.sh 2>&1; then
    echo "   ✅ verify_mtls.sh"
else
    echo "   ❌ verify_mtls.sh has errors"
    FAILED=1
fi

# Test 5: Scripts executable
echo ""
echo "[5/6] Checking script permissions..."
if [ -x scripts/generate_certs.sh ]; then
    echo "   ✅ generate_certs.sh executable"
else
    echo "   ⚠️  Making generate_certs.sh executable..."
    chmod +x scripts/generate_certs.sh
    echo "   ✅ Fixed"
fi

if [ -x scripts/verify_mtls.sh ]; then
    echo "   ✅ verify_mtls.sh executable"
else
    echo "   ⚠️  Making verify_mtls.sh executable..."
    chmod +x scripts/verify_mtls.sh
    echo "   ✅ Fixed"
fi

# Test 6: Caddyfile has mTLS config
echo ""
echo "[6/6] Checking Caddyfile mTLS configuration..."
if grep -q "client_auth" Caddyfile.prod_brutal; then
    echo "   ✅ PASS - client_auth found"
else
    echo "   ❌ FAIL - client_auth not found"
    FAILED=1
fi

if grep -q "require_and_verify" Caddyfile.prod_brutal; then
    echo "   ✅ PASS - require_and_verify found"
else
    echo "   ❌ FAIL - require_and_verify not found"
    FAILED=1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - DEL A VALIDATED"
    echo "════════════════════════════════════════════════════════════"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    echo "════════════════════════════════════════════════════════════"
    exit 1
fi

