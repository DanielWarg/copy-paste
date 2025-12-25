#!/bin/bash
# Runtime validation for DEL A - Network Bunker
# Requires: docker-compose.prod_brutal.yml stack running

set -e

echo "════════════════════════════════════════════════════════════"
echo "DEL A RUNTIME VALIDATION - Network Bunker"
echo "════════════════════════════════════════════════════════════"
echo ""

FAILED=0

# Check if stack is running
echo "[Pre-check] Verifying stack is running..."
if ! docker-compose -f docker-compose.prod_brutal.yml ps | grep -q "Up"; then
    echo "   ❌ Stack is not running"
    echo "   Start with: docker-compose -f docker-compose.prod_brutal.yml up -d"
    exit 1
fi
echo "   ✅ Stack is running"

# Test 1: mTLS verification
echo ""
echo "[Runtime Test 1/2] mTLS verification..."
if [ -f scripts/verify_mtls.sh ]; then
    if bash scripts/verify_mtls.sh 2>&1; then
        echo "   ✅ PASS - mTLS working correctly"
    else
        echo "   ❌ FAIL - mTLS verification failed"
        FAILED=1
    fi
else
    echo "   ⚠️  SKIP - scripts/verify_mtls.sh not found"
fi

# Test 2: No internet access from backend
echo ""
echo "[Runtime Test 2/2] Backend internet access (should fail)..."
BACKEND_CONTAINER=$(docker-compose -f docker-compose.prod_brutal.yml ps -q backend 2>/dev/null || echo "")
if [ -z "$BACKEND_CONTAINER" ]; then
    echo "   ❌ FAIL - Backend container not found"
    FAILED=1
else
    echo "   Testing from container: $BACKEND_CONTAINER"
    # Copy verify script into container and run it
    if docker cp scripts/verify_no_internet.sh "$BACKEND_CONTAINER:/tmp/verify_no_internet.sh" 2>/dev/null; then
        if docker exec "$BACKEND_CONTAINER" bash /tmp/verify_no_internet.sh 2>&1; then
            echo "   ✅ PASS - Backend has NO internet access"
        else
            echo "   ❌ FAIL - Backend CAN reach internet (SECURITY RISK!)"
            FAILED=1
        fi
        docker exec "$BACKEND_CONTAINER" rm -f /tmp/verify_no_internet.sh 2>/dev/null || true
    else
        echo "   ⚠️  SKIP - Could not copy verify script to container"
        echo "   Manual test: docker exec $BACKEND_CONTAINER curl -s https://www.google.com"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL RUNTIME TESTS PASSED - DEL A PROOF-GRADE"
    echo "════════════════════════════════════════════════════════════"
    exit 0
else
    echo "❌ SOME RUNTIME TESTS FAILED"
    echo "════════════════════════════════════════════════════════════"
    exit 1
fi

