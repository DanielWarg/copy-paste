#!/bin/bash
# Rotate a user certificate (create new, old cert remains valid until revocation)
# Usage: ./scripts/cert_rotate.sh <user_id> [days_valid]
# Example: ./scripts/cert_rotate.sh "user-123" 90

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <user_id> [days_valid]"
    echo "  user_id: User identifier (CN in certificate)"
    echo "  days_valid: Certificate validity period (default: 90 days)"
    exit 1
fi

USER_ID="$1"
DAYS_VALID="${2:-90}"

CERT_DIR="certs"
OLD_CERT="${CERT_DIR}/${USER_ID}.crt"
OLD_KEY="${CERT_DIR}/${USER_ID}.key"
NEW_CERT="${CERT_DIR}/${USER_ID}.new.crt"
NEW_KEY="${CERT_DIR}/${USER_ID}.new.key"

# Check old cert exists
if [ ! -f "${OLD_CERT}" ]; then
    echo "❌ ERROR: Certificate not found for user: ${USER_ID}"
    exit 1
fi

# Extract role from old certificate
ROLE=$(openssl x509 -in "${OLD_CERT}" -noout -subject | sed -n 's/.*OU=\([^,]*\).*/\1/p')
if [ -z "$ROLE" ]; then
    echo "❌ ERROR: Could not extract role from old certificate"
    exit 1
fi

echo "Rotating certificate for user: ${USER_ID}, role: ${ROLE}"
echo "Old certificate will remain valid until explicitly revoked"
echo ""

# Create new certificate
echo "1. Creating new certificate..."
./scripts/cert_create.sh "${USER_ID}" "${ROLE}" "${DAYS_VALID}"

# Rename new files
mv "${CERT_DIR}/${USER_ID}.key" "${NEW_KEY}"
mv "${CERT_DIR}/${USER_ID}.crt" "${NEW_CERT}"

echo ""
echo "✅ New certificate created!"
echo ""
echo "Files:"
echo "  - Old key: ${OLD_KEY}"
echo "  - Old cert: ${OLD_CERT}"
echo "  - New key: ${NEW_KEY}"
echo "  - New cert: ${NEW_CERT}"
echo ""
echo "⚠️  NEXT STEPS:"
echo "  1. Distribute new certificate to user securely"
echo "  2. User installs new certificate on their machine"
echo "  3. After user confirms new cert works, revoke old cert:"
echo "     ./scripts/cert_revoke.sh ${USER_ID} --old"
echo "  4. After revocation, rename new files:"
echo "     mv ${NEW_KEY} ${OLD_KEY}"
echo "     mv ${NEW_CERT} ${OLD_CERT}"

