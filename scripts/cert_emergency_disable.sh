#!/bin/bash
# Emergency disable a user certificate (immediate revocation + logging)
# Usage: ./scripts/cert_emergency_disable.sh <user_id> <reason>
# Example: ./scripts/cert_emergency_disable.sh "user-123" "Security incident"

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <user_id> <reason>"
    echo "  user_id: User identifier (CN in certificate)"
    echo "  reason: Reason for emergency disable (e.g., 'Security incident', 'Lost device')"
    exit 1
fi

USER_ID="$1"
REASON="$2"

CERT_DIR="certs"
EMERGENCY_LOG="${CERT_DIR}/emergency-access.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "⚠️  EMERGENCY DISABLE - User: ${USER_ID}"
echo "   Reason: ${REASON}"
echo "   Timestamp: ${TIMESTAMP}"
echo ""
echo "This will immediately revoke the certificate and log the action."
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Log emergency action
echo "${TIMESTAMP}|${USER_ID}|EMERGENCY_DISABLE|${REASON}" >> "${EMERGENCY_LOG}"

# Revoke certificate
echo ""
echo "Revoking certificate..."
./scripts/cert_revoke.sh "${USER_ID}"

echo ""
echo "✅ Emergency disable complete!"
echo ""
echo "⚠️  ACTIONS TAKEN:"
echo "  1. Certificate revoked"
echo "  2. CRL updated"
echo "  3. Emergency action logged: ${EMERGENCY_LOG}"
echo ""
echo "⚠️  NEXT STEPS:"
echo "  1. Restart proxy immediately:"
echo "     docker-compose -f docker-compose.prod_brutal.yml restart proxy"
echo "  2. Notify security team"
echo "  3. Document incident"
echo "  4. Review emergency log: ${EMERGENCY_LOG}"

