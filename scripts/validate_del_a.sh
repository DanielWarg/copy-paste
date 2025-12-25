#!/bin/bash
# Static validation of DEL A (Network Bunker) configuration
# Validates docker-compose.prod_brutal.yml and Caddyfile.prod_brutal

set -e

COMPOSE_FILE="docker-compose.prod_brutal.yml"
CADDYFILE="Caddyfile.prod_brutal"

echo "Validating DEL A (Network Bunker) configuration..."
echo ""

# Check files exist
if [ ! -f "${COMPOSE_FILE}" ]; then
    echo "❌ FAIL: ${COMPOSE_FILE} not found"
    exit 1
fi

if [ ! -f "${CADDYFILE}" ]; then
    echo "❌ FAIL: ${CADDYFILE} not found"
    exit 1
fi

# Validate docker-compose.prod_brutal.yml
echo "1. Validating ${COMPOSE_FILE}..."

# Check backend has no ports
if grep -A 20 "backend:" "${COMPOSE_FILE}" | grep -q "^[[:space:]]*ports:"; then
    echo "❌ FAIL: Backend service has ports exposed (should have no ports)"
    exit 1
fi
echo "   ✅ Backend has no ports"

# Check backend is on internal_net only
if ! grep -A 20 "backend:" "${COMPOSE_FILE}" | grep -q "internal_net"; then
    echo "❌ FAIL: Backend service not on internal_net"
    exit 1
fi
echo "   ✅ Backend on internal_net"

# Check internal_net is internal: true
if ! grep -A 5 "internal_net:" "${COMPOSE_FILE}" | grep -q "internal: true"; then
    echo "❌ FAIL: internal_net is not internal: true"
    exit 1
fi
echo "   ✅ internal_net is internal: true"

# Check proxy exposes ports 443/80
if ! grep -A 10 "proxy:" "${COMPOSE_FILE}" | grep -q "443:443"; then
    echo "❌ FAIL: Proxy does not expose port 443"
    exit 1
fi
echo "   ✅ Proxy exposes 443"

if ! grep -A 10 "proxy:" "${COMPOSE_FILE}" | grep -q "80:80"; then
    echo "❌ FAIL: Proxy does not expose port 80"
    exit 1
fi
echo "   ✅ Proxy exposes 80"

# Check security hardening
if ! grep -A 20 "backend:" "${COMPOSE_FILE}" | grep -q "read_only: true"; then
    echo "❌ FAIL: Backend does not have read_only: true"
    exit 1
fi
echo "   ✅ Backend read_only: true"

if ! grep -A 35 "backend:" "${COMPOSE_FILE}" | grep -q "cap_drop"; then
    echo "❌ FAIL: Backend does not have cap_drop"
    exit 1
fi
echo "   ✅ Backend has cap_drop"

# Validate Caddyfile.prod_brutal
echo ""
echo "2. Validating ${CADDYFILE}..."

# Check client_auth is set
if ! grep -q "client_auth" "${CADDYFILE}"; then
    echo "❌ FAIL: Caddyfile does not have client_auth"
    exit 1
fi
echo "   ✅ Caddyfile has client_auth"

# Check require_and_verify
if ! grep -A 5 "client_auth" "${CADDYFILE}" | grep -q "require_and_verify"; then
    echo "❌ FAIL: Caddyfile client_auth is not require_and_verify"
    exit 1
fi
echo "   ✅ client_auth is require_and_verify"

echo ""
echo "✅ Static validation passed!"

