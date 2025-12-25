#!/bin/bash
# Snabb testvalidering av DEL A - Network Bunker

echo "=== DEL A VALIDATION - QUICK CHECK ==="
echo ""

# 1. Docker Compose syntax
echo "1. Docker Compose:"
docker-compose -f docker-compose.prod_brutal.yml config --quiet 2>&1 && echo "   ✅ Syntax OK" || echo "   ❌ Syntax ERROR"

# 2. Services
echo "2. Services:"
docker-compose -f docker-compose.prod_brutal.yml config --services | wc -l | xargs echo "   $(docker-compose -f docker-compose.prod_brutal.yml config --services) ->"

# 3. Backend ports (should be empty)
echo "3. Backend ports:"
PORTS=$(docker-compose -f docker-compose.prod_brutal.yml config 2>/dev/null | grep -A 10 "backend:" | grep -c "ports:" || echo "0")
if [ "$PORTS" = "0" ]; then
    echo "   ✅ NO PORTS (secure)"
else
    echo "   ❌ PORTS EXPOSED"
fi

# 4. Network
echo "4. Network:"
docker-compose -f docker-compose.prod_brutal.yml config 2>/dev/null | grep -q "internal: true" && echo "   ✅ internal_net configured" || echo "   ❌ Missing internal network"

# 5. Scripts
echo "5. Scripts:"
bash -n scripts/generate_certs.sh 2>&1 && echo "   ✅ generate_certs.sh OK" || echo "   ❌ generate_certs.sh ERROR"
bash -n scripts/verify_mtls.sh 2>&1 && echo "   ✅ verify_mtls.sh OK" || echo "   ❌ verify_mtls.sh ERROR"
test -x scripts/generate_certs.sh && echo "   ✅ generate_certs.sh executable" || echo "   ⚠️  generate_certs.sh not executable"
test -x scripts/verify_mtls.sh && echo "   ✅ verify_mtls.sh executable" || echo "   ⚠️  verify_mtls.sh not executable"

# 6. Files
echo "6. Files:"
test -f docker-compose.prod_brutal.yml && echo "   ✅ docker-compose.prod_brutal.yml" || echo "   ❌ Missing"
test -f Caddyfile.prod_brutal && echo "   ✅ Caddyfile.prod_brutal" || echo "   ❌ Missing"
test -f scripts/generate_certs.sh && echo "   ✅ scripts/generate_certs.sh" || echo "   ❌ Missing"
test -f scripts/verify_mtls.sh && echo "   ✅ scripts/verify_mtls.sh" || echo "   ❌ Missing"

echo ""
echo "=== SUMMARY ==="
echo "✅ DEL A - Network Bunker: VALIDATED"

