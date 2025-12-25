#!/bin/bash
# Phase B Runtime Verification - End-to-end verification with evidence pack
# This script runs the complete Phase B verification and creates evidence documentation

# Don't use set -e here - we need to handle errors manually to capture logs
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
EVIDENCE_FILE="${PROJECT_ROOT}/docs/PHASE_B_RUNTIME_EVIDENCE.md"
LOG_FILE="${PROJECT_ROOT}/phase_b_verification.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Global failure tracking
FAILED=0
FAIL_REASON=""
FAIL_CMD=""
VERIFICATION_EXIT_CODE=0

# Initialize log file
exec > >(tee -a "${LOG_FILE}")
exec 2>&1

# Helper function: Run a step and track failures
# Usage: run_step "Step Name" -- command arg1 arg2 ...
# All arguments after -- are executed as a real command (array-based, safe for spaces in paths)
run_step() {
    local step_name="$1"
    shift
    
    # Check for -- separator
    if [ "$1" != "--" ]; then
        echo -e "${RED}❌ ERROR: run_step requires '--' separator${NC}"
        echo "Usage: run_step \"Name\" -- command arg1 arg2 ..."
        FAILED=1
        FAIL_REASON="${step_name} (invalid usage)"
        FAIL_CMD="run_step called incorrectly"
        return 1
    fi
    
    shift  # Remove --
    
    # Build command array and quoted string for display
    local cmd_array=("$@")
    local cmd_display=""
    for arg in "${cmd_array[@]}"; do
        # Use printf %q for safe quoting in display
        if [ -z "$cmd_display" ]; then
            cmd_display=$(printf '%q' "$arg")
        else
            cmd_display="${cmd_display} $(printf '%q' "$arg")"
        fi
    done
    
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Step: ${step_name}"
    echo "════════════════════════════════════════════════════════════"
    echo "Command: ${cmd_display}"
    echo ""
    
    # Run the command array directly (no eval, safe for spaces)
    "${cmd_array[@]}"
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        FAILED=1
        FAIL_REASON="${step_name}"
        FAIL_CMD="${cmd_display}"
        echo ""
        echo -e "${RED}❌ FAILED: ${step_name}${NC}"
        echo "Exit code: ${exit_code}"
        echo "Command: ${cmd_display}"
        return $exit_code
    else
        echo ""
        echo -e "${GREEN}✅ PASSED: ${step_name}${NC}"
        return 0
    fi
}

echo "════════════════════════════════════════════════════════════"
echo "Phase B Runtime Verification"
echo "════════════════════════════════════════════════════════════"
echo ""

# Step 1: Pre-flight checks
echo "Step 1/5: Pre-flight checks..."
echo ""

# Check repo path doesn't contain ':' (use validation script)
# FAIL-FAST: This must run first and fail immediately if path is invalid
echo "Validating repository path (fail-fast)..."
if ! bash "${PROJECT_ROOT}/scripts/validate_repo_path.sh"; then
    echo ""
    echo "SOLUTION:"
    echo "  1. Rename the repository folder to remove ':'"
    echo "  2. Example: COPY:PASTE → COPY-PASTE"
    echo "  3. See: docs/REPO_PATH_FIX.md for complete instructions"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ Repository path validated${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker not found${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker is not running${NC}"
    echo "   Start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✅ Docker is available and running${NC}"

# Check Node/npm
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ ERROR: Node.js not found${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ ERROR: npm not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js and npm are available${NC}"

# Check git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: git not found (cannot record commit hash)${NC}"
    COMMIT_HASH="unknown"
else
    COMMIT_HASH=$(cd "${PROJECT_ROOT}" && git rev-parse HEAD 2>/dev/null || echo "unknown")
fi

echo ""
echo "Step 2/5: Building frontend..."
echo ""

cd "${PROJECT_ROOT}/frontend"

# Install dependencies
if [ -f "package-lock.json" ]; then
    run_step "Frontend: Install dependencies (npm ci)" -- npm ci
else
    run_step "Frontend: Install dependencies (npm install)" -- npm install
fi

# Build frontend
run_step "Frontend: Build" -- npm run build

# Verify dist exists and is not empty
if [ ! -d "dist" ]; then
    FAILED=1
    FAIL_REASON="Frontend: dist directory not created"
    FAIL_CMD="npm run build"
    echo -e "${RED}❌ ERROR: frontend/dist not created${NC}"
elif [ -z "$(ls -A dist)" ]; then
    FAILED=1
    FAIL_REASON="Frontend: dist directory is empty"
    FAIL_CMD="npm run build"
    echo -e "${RED}❌ ERROR: frontend/dist is empty${NC}"
else
    echo -e "${GREEN}✅ Frontend built successfully${NC}"
fi

cd "${PROJECT_ROOT}"

echo ""
echo "Step 3/5: Starting services..."
echo ""

# Stop any existing services
echo "Stopping existing services..."
docker-compose -f docker-compose.prod_brutal.yml down 2>/dev/null || true

# Start services
run_step "Docker: Start services" -- docker-compose -f docker-compose.prod_brutal.yml up -d --build

# Wait for proxy to be ready
echo "Waiting for proxy to be ready..."
TIMEOUT=60
ELAPSED=0
PROXY_READY=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker ps | grep -q "copy-paste-proxy-brutal"; then
        if docker exec copy-paste-proxy-brutal caddy version &>/dev/null; then
            echo -e "${GREEN}✅ Proxy is ready${NC}"
            PROXY_READY=1
            break
        fi
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo "  Waiting... (${ELAPSED}s/${TIMEOUT}s)"
done

if [ $PROXY_READY -eq 0 ]; then
    FAILED=1
    FAIL_REASON="Proxy: Did not start within ${TIMEOUT} seconds"
    FAIL_CMD="docker exec copy-paste-proxy-brutal caddy version"
    echo -e "${RED}❌ ERROR: Proxy did not start within ${TIMEOUT} seconds${NC}"
    echo "Check logs: docker-compose -f docker-compose.prod_brutal.yml logs proxy"
fi

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
BACKEND_READY=0
BACKEND_TIMEOUT=60
BACKEND_ELAPSED=0
while [ $BACKEND_ELAPSED -lt $BACKEND_TIMEOUT ]; do
    # Check if backend container is running (not restarting)
    BACKEND_STATUS=$(docker inspect copy-paste-backend-brutal --format='{{.State.Status}}' 2>/dev/null || echo "unknown")
    if [ "$BACKEND_STATUS" = "running" ]; then
        # Check if backend health endpoint responds (using Python, curl not available in container)
        if docker exec copy-paste-backend-brutal python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" &>/dev/null; then
            echo -e "${GREEN}✅ Backend is ready${NC}"
            BACKEND_READY=1
            break
        fi
    elif [ "$BACKEND_STATUS" = "restarting" ]; then
        echo "  Backend is restarting... (${BACKEND_ELAPSED}s/${BACKEND_TIMEOUT}s)"
        # Show last 10 log lines to help diagnose
        if [ $((BACKEND_ELAPSED % 10)) -eq 0 ]; then
            echo "  Recent backend logs:"
            docker logs --tail 10 copy-paste-backend-brutal 2>&1 | sed 's/^/    /'
        fi
    fi
    sleep 2
    BACKEND_ELAPSED=$((BACKEND_ELAPSED + 2))
done

if [ $BACKEND_READY -eq 0 ]; then
    FAILED=1
    FAIL_REASON="Backend: Did not become ready within ${BACKEND_TIMEOUT} seconds"
    FAIL_CMD="docker exec copy-paste-backend-brutal python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()\""
    echo -e "${RED}❌ ERROR: Backend did not become ready within ${BACKEND_TIMEOUT} seconds${NC}"
    echo ""
    echo "Backend container status:"
    docker inspect copy-paste-backend-brutal --format='Status: {{.State.Status}}, ExitCode: {{.State.ExitCode}}, Error: {{.State.Error}}' 2>/dev/null || echo "Could not inspect container"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Backend container logs (last 50 lines):"
    echo "════════════════════════════════════════════════════════════"
    docker logs --tail 50 copy-paste-backend-brutal 2>&1 || echo "Failed to get backend logs"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Check logs: docker logs copy-paste-backend-brutal"
fi

# Collect Docker info before verification (for evidence pack)
echo "Collecting Docker environment info..."
DOCKER_COMPOSE_PS=$(docker-compose -f docker-compose.prod_brutal.yml ps 2>&1 || echo "Failed to get docker compose ps")
DOCKER_IMAGES=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Digest}}\t{{.ID}}" 2>&1 | grep -E "(copy-paste|REPOSITORY)" || echo "No copy-paste images found")

echo ""
echo "Step 4/5: Running Phase B verification gate..."
echo ""

# Run verification and capture output
VERIFICATION_OUTPUT=$(make verify-phase-b 2>&1)
VERIFICATION_EXIT_CODE=$?

if [ $VERIFICATION_EXIT_CODE -ne 0 ]; then
    FAILED=1
    if [ -z "$FAIL_REASON" ]; then
        FAIL_REASON="Phase B verification gate"
        FAIL_CMD="make verify-phase-b"
    fi
fi

echo "$VERIFICATION_OUTPUT"

# If verification failed, show container logs
if [ $VERIFICATION_EXIT_CODE -ne 0 ] || [ $FAILED -eq 1 ]; then
    echo ""
    echo -e "${RED}❌ Verification gate failed. Showing container logs...${NC}"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Backend container logs (last 200 lines):"
    echo "════════════════════════════════════════════════════════════"
    docker logs --tail 200 copy-paste-backend-brutal 2>&1 || echo "Failed to get backend logs"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Proxy container logs (last 200 lines):"
    echo "════════════════════════════════════════════════════════════"
    docker logs --tail 200 copy-paste-proxy-brutal 2>&1 || echo "Failed to get proxy logs"
    echo ""
fi

echo ""
echo "Step 5/5: Creating evidence pack..."
echo ""

# Get current date/time
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')
DATE_ONLY=$(date '+%Y-%m-%d')
CURRENT_PATH=$(pwd)

# Determine overall result
# PASS only if FAILED=0 AND VERIFICATION_EXIT_CODE=0
if [ $FAILED -eq 0 ] && [ $VERIFICATION_EXIT_CODE -eq 0 ]; then
    OVERALL_RESULT="PASS"
    RESULT_COLOR="${GREEN}"
else
    OVERALL_RESULT="FAIL"
    RESULT_COLOR="${RED}"
fi

# Parse individual test results from output
PHASE_A_RESULT="UNKNOWN"
PRIVACY_RESULT="UNKNOWN"
FRONTEND_RESULT="UNKNOWN"

if echo "$VERIFICATION_OUTPUT" | grep -q "✅ Brutal Security Profile validation complete"; then
    PHASE_A_RESULT="PASS"
else
    PHASE_A_RESULT="FAIL"
fi

if echo "$VERIFICATION_OUTPUT" | grep -q "✅ Privacy chain verification complete"; then
    PRIVACY_RESULT="PASS"
else
    PRIVACY_RESULT="FAIL"
fi

if echo "$VERIFICATION_OUTPUT" | grep -q "✅ Frontend Exposure Verification: PASS"; then
    FRONTEND_RESULT="PASS"
else
    FRONTEND_RESULT="FAIL"
fi

# Create evidence file
cat > "${EVIDENCE_FILE}" << EOF
# Phase B Runtime Verification Evidence

**Datum:** ${DATE_ONLY}  
**Tid:** ${TIMESTAMP}  
**Commit Hash:** ${COMMIT_HASH}  
**Repository Path:** ${CURRENT_PATH}

---

## Overall Result

**Status:** ${OVERALL_RESULT}

EOF

# Add failure information if failed
if [ $FAILED -eq 1 ] || [ $VERIFICATION_EXIT_CODE -ne 0 ]; then
    cat >> "${EVIDENCE_FILE}" << EOF
## Failure Information

**Failed Step:** ${FAIL_REASON:-"Unknown"}  
**Failed Command:** \`${FAIL_CMD:-"Unknown"}\`  
**Verification Exit Code:** ${VERIFICATION_EXIT_CODE}

---

EOF
fi

cat >> "${EVIDENCE_FILE}" << EOF
## Verification Results

### Phase A Regression

**Test:** \`make verify-brutal\`  
**Result:** ${PHASE_A_RESULT}

**Kriterium:** Alla Phase A-tester måste passera (100% pass rate)

---

### Privacy Chain Regression

**Test:** \`make verify-privacy-chain\`  
**Result:** ${PRIVACY_RESULT}

**Kriterium:** Alla privacy chain-tester måste passera (100% pass rate)

---

### Frontend Exposure Verification

**Test:** \`bash scripts/verify_frontend_exposure.sh\`  
**Result:** ${FRONTEND_RESULT}

**Kriterium:** Alla frontend exposure-tester måste passera (100% pass rate)

---

## Docker Environment

### Container Status

\`\`\`
${DOCKER_COMPOSE_PS}
\`\`\`

### Docker Images

\`\`\`
${DOCKER_IMAGES}
\`\`\`

---

## Command Log

\`\`\`
${VERIFICATION_OUTPUT}
\`\`\`

---

## Verification Checklist

- [ ] Phase A regression: ${PHASE_A_RESULT}
- [ ] Privacy chain regression: ${PRIVACY_RESULT}
- [ ] Frontend exposure: ${FRONTEND_RESULT}

---

## Sign-off

**Tech Lead:**
- [ ] Alla tekniska kriterier uppfyllda
- [ ] Phase A regression: ${PHASE_A_RESULT}
- [ ] Phase B verification: ${OVERALL_RESULT}
- Signatur: _________________ Datum: _________________

**Security Lead:**
- [ ] Alla säkerhetskriterier uppfyllda
- [ ] Phase A säkerhetsgarantier intakta
- [ ] Phase B ändrar inte Phase A-komponenter
- Signatur: _________________ Datum: _________________

**Operations:**
- [ ] Production startup procedure fungerar
- [ ] Certificate lifecycle procedures fungerar
- [ ] Incident playbook kan följas
- Signatur: _________________ Datum: _________________

**Product/PO:**
- [ ] Funktionalitet matchar behov
- [ ] Systemet är operativt för produktion
- Signatur: _________________ Datum: _________________

---

## Notes

**Log File:** \`phase_b_verification.log\`

**Next Steps:**
- Review evidence pack
- Complete sign-off checklist
- Document any issues or follow-up actions

---

**This document is a formal record of Phase B runtime verification.**

EOF

echo -e "${GREEN}✅ Evidence pack created: ${EVIDENCE_FILE}${NC}"
echo ""

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "Phase B Runtime Verification: ${RESULT_COLOR}${OVERALL_RESULT}${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Results:"
echo "  - Phase A Regression: ${PHASE_A_RESULT}"
echo "  - Privacy Chain: ${PRIVACY_RESULT}"
echo "  - Frontend Exposure: ${FRONTEND_RESULT}"
if [ $FAILED -eq 1 ]; then
    echo ""
    echo "Failure Details:"
    echo "  - Failed Step: ${FAIL_REASON}"
    echo "  - Failed Command: ${FAIL_CMD}"
fi
echo ""
echo "Evidence pack: ${EVIDENCE_FILE}"
echo "Log file: ${LOG_FILE}"
echo ""

# Determine final exit code
if [ $FAILED -eq 1 ]; then
    FINAL_EXIT_CODE=1
elif [ $VERIFICATION_EXIT_CODE -ne 0 ]; then
    FINAL_EXIT_CODE=$VERIFICATION_EXIT_CODE
else
    FINAL_EXIT_CODE=0
fi

# Write final status line and exit code to log
if [ $FINAL_EXIT_CODE -eq 0 ]; then
    echo "════════════════════════════════════════════════════════════"
    echo "PHASE B RUNTIME: PASS"
    echo "════════════════════════════════════════════════════════════"
    echo "Evidence pack: ${EVIDENCE_FILE}"
    echo "Log file: ${LOG_FILE}"
    echo "EXIT_CODE=0"
    echo "════════════════════════════════════════════════════════════"
    echo -e "${GREEN}✅ Phase B verification complete - Ready for sign-off${NC}"
    exit 0
else
    echo "════════════════════════════════════════════════════════════"
    echo "PHASE B RUNTIME: FAIL"
    echo "════════════════════════════════════════════════════════════"
    echo "Evidence pack: ${EVIDENCE_FILE}"
    echo "Log file: ${LOG_FILE}"
    if [ $FAILED -eq 1 ]; then
        echo "Failed Step: ${FAIL_REASON}"
        echo "Failed Command: ${FAIL_CMD}"
    fi
    echo "EXIT_CODE=${FINAL_EXIT_CODE}"
    echo "════════════════════════════════════════════════════════════"
    echo -e "${RED}❌ Phase B verification failed - Review evidence pack and fix issues${NC}"
    exit $FINAL_EXIT_CODE
fi
