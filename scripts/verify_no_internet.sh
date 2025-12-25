#!/bin/bash
# Verify that backend container has no internet egress
# Should be run INSIDE the backend container

set -e

echo "Verifying no internet egress from backend container..."
echo ""

# Test 1: Try to reach external DNS
echo "Test 1: DNS lookup to 8.8.8.8..."
if timeout 3 nslookup google.com 8.8.8.8 >/dev/null 2>&1; then
    echo "❌ FAIL: DNS lookup succeeded (internet access available)"
    exit 1
else
    echo "✅ PASS: DNS lookup failed (no internet access)"
fi

# Test 2: Try to curl external address
echo ""
echo "Test 2: HTTP request to https://www.google.com..."
if timeout 3 curl -s https://www.google.com >/dev/null 2>&1; then
    echo "❌ FAIL: HTTP request succeeded (internet access available)"
    exit 1
else
    echo "✅ PASS: HTTP request failed (no internet access)"
fi

# Test 3: Try to ping external address
echo ""
echo "Test 3: Ping to 8.8.8.8..."
if timeout 3 ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "❌ FAIL: Ping succeeded (internet access available)"
    exit 1
else
    echo "✅ PASS: Ping failed (no internet access)"
fi

echo ""
echo "✅ No internet egress verification complete!"
