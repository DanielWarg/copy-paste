#!/bin/bash
# Revoke a user certificate and update CRL
# Usage: ./scripts/cert_revoke.sh <user_id> [--old]
# Example: ./scripts/cert_revoke.sh "user-123"
#          ./scripts/cert_revoke.sh "user-123" --old  (revoke old cert during rotation)

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <user_id> [--old]"
    echo "  user_id: User identifier (CN in certificate)"
    echo "  --old: Revoke old certificate (during rotation)"
    exit 1
fi

USER_ID="$1"
REVOKE_OLD="${2:-}"

CERT_DIR="certs"
CA_KEY="${CERT_DIR}/ca.key"
CA_CERT="${CERT_DIR}/ca.crt"
CRL_FILE="${CERT_DIR}/crl.pem"
CRL_DB="${CERT_DIR}/crl_index.txt"
CRL_SERIAL="${CERT_DIR}/crl_serial.txt"

if [ "$REVOKE_OLD" = "--old" ]; then
    CERT_FILE="${CERT_DIR}/${USER_ID}.crt"
    CERT_LABEL="old certificate"
else
    CERT_FILE="${CERT_DIR}/${USER_ID}.crt"
    CERT_LABEL="certificate"
fi

# Check certificate exists
if [ ! -f "${CERT_FILE}" ]; then
    echo "❌ ERROR: Certificate not found: ${CERT_FILE}"
    exit 1
fi

# Check CA exists
if [ ! -f "${CA_KEY}" ] || [ ! -f "${CA_CERT}" ]; then
    echo "❌ ERROR: CA certificate not found. Run ./scripts/generate_certs.sh first"
    exit 1
fi

echo "Revoking ${CERT_LABEL} for user: ${USER_ID}"
echo ""

# Initialize CRL if it doesn't exist
if [ ! -f "${CRL_FILE}" ]; then
    echo "1. Initializing CRL..."
    touch "${CRL_DB}"
    echo "01" > "${CRL_SERIAL}"
    openssl ca -gencrl -keyfile "${CA_KEY}" -cert "${CA_CERT}" \
        -out "${CRL_FILE}" -config <(
            echo "[ca]"
            echo "default_ca = CA_default"
            echo "[CA_default]"
            echo "dir = ${CERT_DIR}"
            echo "database = ${CRL_DB}"
            echo "serial = ${CRL_SERIAL}"
            echo "crlnumber = ${CRL_SERIAL}"
        ) 2>/dev/null || {
        # Fallback: create CRL without config file
        openssl ca -gencrl -keyfile "${CA_KEY}" -cert "${CA_CERT}" -out "${CRL_FILE}"
    }
fi

# Revoke certificate
echo "2. Revoking certificate..."
openssl ca -revoke "${CERT_FILE}" -keyfile "${CA_KEY}" -cert "${CA_CERT}" \
    -config <(
        echo "[ca]"
        echo "default_ca = CA_default"
        echo "[CA_default]"
        echo "dir = ${CERT_DIR}"
        echo "database = ${CRL_DB}"
        echo "serial = ${CRL_SERIAL}"
    ) 2>/dev/null || {
    # Fallback: manual revocation
    echo "   Using manual revocation method..."
    SERIAL=$(openssl x509 -in "${CERT_FILE}" -noout -serial | cut -d= -f2)
    echo "R\t$(date +%y%m%d%H%M%S%z)\t${SERIAL}\tunknown\t${USER_ID}" >> "${CRL_DB}"
}

# Update CRL
echo "3. Updating CRL..."
openssl ca -gencrl -keyfile "${CA_KEY}" -cert "${CA_CERT}" \
    -out "${CRL_FILE}" -config <(
        echo "[ca]"
        echo "default_ca = CA_default"
        echo "[CA_default]"
        echo "dir = ${CERT_DIR}"
        echo "database = ${CRL_DB}"
        echo "serial = ${CRL_SERIAL}"
    ) 2>/dev/null || {
    # Fallback: regenerate CRL
    openssl ca -gencrl -keyfile "${CA_KEY}" -cert "${CA_CERT}" -out "${CRL_FILE}"
}

# Set permissions
chmod 644 "${CRL_FILE}"

echo ""
echo "✅ Certificate revoked successfully!"
echo ""
echo "⚠️  IMPORTANT:"
echo "  1. CRL updated: ${CRL_FILE}"
echo "  2. Restart proxy to load new CRL:"
echo "     docker-compose -f docker-compose.prod_brutal.yml restart proxy"
echo "  3. Revoked certificate will be rejected within 5 minutes"
echo "  4. Document revocation in audit log"

