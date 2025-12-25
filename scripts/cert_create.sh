#!/bin/bash
# Create a new user certificate with CN=user_id and OU=role
# Usage: ./scripts/cert_create.sh <user_id> <role> [days_valid]
# Example: ./scripts/cert_create.sh "user-123" "journalist" 90

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <user_id> <role> [days_valid]"
    echo "  user_id: User identifier (CN in certificate)"
    echo "  role: User role (OU in certificate) - journalist, redaktör, admin"
    echo "  days_valid: Certificate validity period (default: 90 days)"
    exit 1
fi

USER_ID="$1"
ROLE="$2"
DAYS_VALID="${3:-90}"

CERT_DIR="certs"
CA_KEY="${CERT_DIR}/ca.key"
CA_CERT="${CERT_DIR}/ca.crt"
USER_KEY="${CERT_DIR}/${USER_ID}.key"
USER_CSR="${CERT_DIR}/${USER_ID}.csr"
USER_CERT="${CERT_DIR}/${USER_ID}.crt"

# Validate role
if [[ ! "$ROLE" =~ ^(journalist|redaktör|admin)$ ]]; then
    echo "❌ ERROR: Invalid role '$ROLE'. Must be: journalist, redaktör, or admin"
    exit 1
fi

# Check CA exists
if [ ! -f "${CA_KEY}" ] || [ ! -f "${CA_CERT}" ]; then
    echo "❌ ERROR: CA certificate not found. Run ./scripts/generate_certs.sh first"
    exit 1
fi

echo "Creating certificate for user: ${USER_ID}, role: ${ROLE}, valid for ${DAYS_VALID} days"
echo ""

# Generate user private key
echo "1. Generating private key..."
openssl genrsa -out "${USER_KEY}" 4096

# Generate CSR
echo "2. Generating certificate signing request..."
openssl req -new -key "${USER_KEY}" -out "${USER_CSR}" \
    -subj "/C=SE/ST=Stockholm/L=Stockholm/O=CopyPaste/OU=${ROLE}/CN=${USER_ID}"

# Generate certificate signed by CA
echo "3. Signing certificate with CA..."
openssl x509 -req -days "${DAYS_VALID}" -in "${USER_CSR}" -CA "${CA_CERT}" -CAkey "${CA_KEY}" \
    -CAcreateserial -out "${USER_CERT}" \
    -extensions v3_req -extfile <(
        echo "[v3_req]"
        echo "keyUsage = digitalSignature, keyEncipherment"
        echo "extendedKeyUsage = clientAuth"
    )

# Clean up CSR
rm -f "${USER_CSR}"

# Set permissions
chmod 600 "${USER_KEY}"
chmod 644 "${USER_CERT}"

echo ""
echo "✅ Certificate created successfully!"
echo ""
echo "Files created:"
echo "  - Private key: ${USER_KEY}"
echo "  - Certificate: ${USER_CERT}"
echo ""
echo "⚠️  IMPORTANT:"
echo "  1. Distribute certificate securely (USB, encrypted email)"
echo "  2. Keep private key secure (user should install on their machine)"
echo "  3. Certificate is valid for ${DAYS_VALID} days"
echo "  4. Document certificate creation in audit log"

