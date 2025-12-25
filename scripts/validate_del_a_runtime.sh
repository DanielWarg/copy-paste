#!/bin/bash
# Runtime validation of DEL A (Network Bunker)
# Tests mTLS and no-egress

set -e

COMPOSE_FILE="docker-compose.prod_brutal.yml"
CONTAINER_NAME="copy-paste-backend-brutal"

echo "Runtime validation of DEL A (Network Bunker)..."
echo ""

# Check if containers are running
if ! docker ps | grep -q "${CONTAINER_NAME}"; then
    echo "⚠️  WARN: Backend container not running"
    echo "   Start with: docker-compose -f ${COMPOSE_FILE} up -d"
    exit 1
fi

# Test 1: mTLS verification
echo "1. Testing mTLS..."
if [ -f "scripts/verify_mtls.sh" ]; then
    bash scripts/verify_mtls.sh || exit 1
else
    echo "⚠️  WARN: verify_mtls.sh not found, skipping mTLS test"
fi

echo ""

# Test 2: No internet egress
echo "2. Testing no internet egress..."
if [ -f "scripts/verify_no_internet.sh" ]; then
    docker exec "${CONTAINER_NAME}" bash scripts/verify_no_internet.sh || exit 1
else
    echo "⚠️  WARN: verify_no_internet.sh not found, skipping egress test"
    echo "   Manual test: docker exec ${CONTAINER_NAME} curl -s https://www.google.com"
    echo "   Should fail with connection error"
fi

echo ""
echo "✅ Runtime validation complete!"

