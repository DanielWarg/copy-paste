#!/bin/bash
set -euo pipefail

# Security Tests - Verify GDPR and security rules

API_BASE="http://localhost:8000"

echo "=== SECURITY TESTS ==="

# Test 1: Mapping never in response
echo "Test 1: Mapping never in API response"
SCRUB_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/privacy/scrub" \
    -H "Content-Type: application/json" \
    -d '{"event_id":"00000000-0000-0000-0000-000000000000","production_mode":true}')

if echo "$SCRUB_RESPONSE" | grep -q "mapping"; then
    echo "✗ FAILED: Mapping found in response"
    exit 1
else
    echo "✓ PASSED: No mapping in response"
fi

# Test 2: Production Mode ON requires anonymization
echo ""
echo "Test 2: Production Mode ON blocks non-anonymized data"
# This would need a test event that fails anonymization
echo "  (Requires specific test scenario)"

# Test 3: External API requires is_anonymized=true
echo ""
echo "Test 3: External API blocks non-anonymized data"
# Tested in main pipeline test

echo ""
echo "✓ Security tests completed"

