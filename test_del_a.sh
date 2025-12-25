#!/bin/bash
# Testvalidering DEL A - Network Bunker med progress-indikatorer

set -e

echo "════════════════════════════════════════════════════════════"
echo "DEL A VALIDATION - Network Bunker"
echo "════════════════════════════════════════════════════════════"
echo ""

# Function to print progress
progress() {
    echo "[$(date +%H:%M:%S)] $1"
}

# Test 1: Docker Compose syntax
progress "Test 1/7: Validating Docker Compose syntax..."
if timeout 5 docker-compose -f docker-compose.prod_brutal.yml config --quiet 2>&1 > /dev/null; then
    echo "   ✅ PASS - Syntax valid"
else
    echo "   ❌ FAIL - Syntax error or timeout"
    exit 1
fi

# Test 2: Services count
progress "Test 2/7: Checking services..."
SERVICES=$(timeout 5 docker-compose -f docker-compose.prod_brutal.yml config --services 2>/dev/null | wc -l | tr -d ' ')
if [ "$SERVICES" = "3" ]; then
    echo "   ✅ PASS - 3 services found (postgres, backend, proxy)"
else
    echo "   ❌ FAIL - Expected 3 services, found $SERVICES"
    exit 1
fi

# Test 3: Backend ports (should be none)
progress "Test 3/7: Checking backend ports (should be none)..."
if timeout 5 docker-compose -f docker-compose.prod_brutal.yml config 2>/dev/null | grep -A 15 "backend:" | grep -q "^[[:space:]]*ports:"; then
    echo "   ❌ FAIL - Backend has ports exposed"
    exit 1
else
    echo "   ✅ PASS - Backend has no ports (secure)"
fi

# Test 4: Internal network
progress "Test 4/7: Checking internal network configuration..."
if timeout 5 docker-compose -f docker-compose.prod_brutal.yml config 2>/dev/null | grep -q "internal: true"; then
    echo "   ✅ PASS - internal_net configured with internal: true"
else
    echo "   ❌ FAIL - internal network not configured correctly"
    exit 1
fi

# Test 5: Scripts syntax
progress "Test 5/7: Validating script syntax..."
if bash -n scripts/generate_certs.sh 2>&1 > /dev/null; then
    echo "   ✅ PASS - generate_certs.sh syntax valid"
else
    echo "   ❌ FAIL - generate_certs.sh has syntax errors"
    exit 1
fi

if bash -n scripts/verify_mtls.sh 2>&1 > /dev/null; then
    echo "   ✅ PASS - verify_mtls.sh syntax valid"
else
    echo "   ❌ FAIL - verify_mtls.sh has syntax errors"
    exit 1
fi

# Test 6: Scripts executable
progress "Test 6/7: Checking script permissions..."
if [ -x scripts/generate_certs.sh ]; then
    echo "   ✅ PASS - generate_certs.sh is executable"
else
    echo "   ⚠️  WARN - generate_certs.sh not executable (fixing...)"
    chmod +x scripts/generate_certs.sh
    echo "   ✅ FIXED - generate_certs.sh is now executable"
fi

if [ -x scripts/verify_mtls.sh ]; then
    echo "   ✅ PASS - verify_mtls.sh is executable"
else
    echo "   ⚠️  WARN - verify_mtls.sh not executable (fixing...)"
    chmod +x scripts/verify_mtls.sh
    echo "   ✅ FIXED - verify_mtls.sh is now executable"
fi

# Test 7: Required files exist
progress "Test 7/7: Checking required files..."
FILES=("docker-compose.prod_brutal.yml" "Caddyfile.prod_brutal" "scripts/generate_certs.sh" "scripts/verify_mtls.sh")
ALL_OK=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file MISSING"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = false ]; then
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ ALL TESTS PASSED - DEL A VALIDATED"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  - Docker Compose: ✅ Valid"
echo "  - Services: ✅ 3 services"
echo "  - Backend security: ✅ No ports, internal network"
echo "  - Scripts: ✅ Valid syntax, executable"
echo "  - Files: ✅ All present"
echo ""

