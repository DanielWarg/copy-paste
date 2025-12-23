#!/bin/bash
set -euo pipefail

# Full Pipeline Test - No Mocks, Real Data Only
# Tests: Ingest → Scrub → Draft

API_BASE="http://localhost:8000"
TEST_REPORT="test_report.txt"

echo "=== COPY/PASTE FULL PIPELINE TEST ===" > "$TEST_REPORT"
echo "Started: $(date)" >> "$TEST_REPORT"
echo "" >> "$TEST_REPORT"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

test_step() {
    local name="$1"
    local command="$2"
    
    echo -e "${YELLOW}Testing: $name${NC}"
    echo "Test: $name" >> "$TEST_REPORT"
    
    if eval "$command"; then
        echo -e "${GREEN}✓ PASSED: $name${NC}"
        echo "  Result: PASSED" >> "$TEST_REPORT"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED: $name${NC}"
        echo "  Result: FAILED" >> "$TEST_REPORT"
        ((FAILED++))
        return 1
    fi
}

# Test 1: Health Check
test_step "Health Check" "curl -s -f $API_BASE/health | grep -q '\"status\":\"ok\"'"

# Test 2: Ingest Text
echo ""
echo "=== TEST 2: Ingest Text ==="
TEST_TEXT="John Doe works at Acme Corp. Contact: john@acme.com or call 555-1234. Address: 123 Main St, Stockholm."
INGEST_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/ingest" \
    -H "Content-Type: application/json" \
    -d "{\"input_type\":\"text\",\"value\":\"$TEST_TEXT\"}")

EVENT_ID=$(echo "$INGEST_RESPONSE" | grep -o '"event_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$EVENT_ID" ]; then
    echo -e "${RED}✗ FAILED: Could not extract event_id${NC}"
    echo "$INGEST_RESPONSE"
    ((FAILED++))
    exit 1
fi

echo "Event ID: $EVENT_ID"
test_step "Ingest Text" "[ -n \"$EVENT_ID\" ]"

# Test 3: Scrub with Production Mode ON
echo ""
echo "=== TEST 3: Scrub (Production Mode ON) ==="
SCRUB_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/privacy/scrub" \
    -H "Content-Type: application/json" \
    -d "{\"event_id\":\"$EVENT_ID\",\"production_mode\":true}")

CLEAN_TEXT=$(echo "$SCRUB_RESPONSE" | grep -o '"clean_text":"[^"]*"' | cut -d'"' -f4)
IS_ANONYMIZED=$(echo "$SCRUB_RESPONSE" | grep -o '"is_anonymized":[^,}]*' | grep -o 'true\|false')

echo "Clean text: ${CLEAN_TEXT:0:100}..."
echo "Is anonymized: $IS_ANONYMIZED"

test_step "Scrub returns is_anonymized=true" "[ \"$IS_ANONYMIZED\" = \"true\" ]"
test_step "Scrub contains anonymization tokens" "echo \"$CLEAN_TEXT\" | grep -q '\[PERSON\|\[ORG\|\[EMAIL\|\[PHONE'"

# Test 4: Scrub with Production Mode OFF
echo ""
echo "=== TEST 4: Scrub (Production Mode OFF) ==="
SCRUB_RESPONSE_OFF=$(curl -s -X POST "$API_BASE/api/v1/privacy/scrub" \
    -H "Content-Type: application/json" \
    -d "{\"event_id\":\"$EVENT_ID\",\"production_mode\":false}")

IS_ANONYMIZED_OFF=$(echo "$SCRUB_RESPONSE_OFF" | grep -o '"is_anonymized":[^,}]*' | grep -o 'true\|false')
echo "Is anonymized (OFF mode): $IS_ANONYMIZED_OFF"

# Test 5: Draft Generation (requires OpenAI API key)
echo ""
echo "=== TEST 5: Draft Generation ==="
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo -e "${YELLOW}⚠ SKIPPED: OPENAI_API_KEY not set${NC}"
    echo "  Test: Draft Generation - SKIPPED (no API key)" >> "$TEST_REPORT"
else
    DRAFT_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/draft/generate" \
        -H "Content-Type: application/json" \
        -d "{\"event_id\":\"$EVENT_ID\",\"clean_text\":\"$CLEAN_TEXT\",\"production_mode\":true}")
    
    DRAFT_TEXT=$(echo "$DRAFT_RESPONSE" | grep -o '"text":"[^"]*"' | cut -d'"' -f4)
    CITATIONS=$(echo "$DRAFT_RESPONSE" | grep -o '"citations":\[[^]]*\]')
    
    test_step "Draft generation succeeds" "[ -n \"$DRAFT_TEXT\" ]"
    test_step "Draft contains citations" "echo \"$DRAFT_RESPONSE\" | grep -q 'citations'"
fi

# Test 6: Security - Try to call draft without anonymization
echo ""
echo "=== TEST 6: Security Test (Block unscrubbed data) ==="
SECURITY_TEST=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/api/v1/draft/generate" \
    -H "Content-Type: application/json" \
    -d "{\"event_id\":\"$EVENT_ID\",\"clean_text\":\"$TEST_TEXT\",\"production_mode\":false}")

HTTP_CODE=$(echo "$SECURITY_TEST" | tail -n1)
test_step "Security blocks unscrubbed data" "[ \"$HTTP_CODE\" = \"400\" ]"

# Summary
echo ""
echo "=== TEST SUMMARY ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "" >> "$TEST_REPORT"
echo "=== SUMMARY ===" >> "$TEST_REPORT"
echo "Passed: $PASSED" >> "$TEST_REPORT"
echo "Failed: $FAILED" >> "$TEST_REPORT"
echo "Completed: $(date)" >> "$TEST_REPORT"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

