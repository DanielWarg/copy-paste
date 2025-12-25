#!/bin/bash
# Generate CA, server, and client certificates for mTLS
# Usage: ./scripts/generate_certs.sh

set -e

CERT_DIR="certs"
CA_KEY="${CERT_DIR}/ca.key"
CA_CERT="${CERT_DIR}/ca.crt"
SERVER_KEY="${CERT_DIR}/server.key"
SERVER_CSR="${CERT_DIR}/server.csr"
SERVER_CERT="${CERT_DIR}/server.crt"
CLIENT_KEY="${CERT_DIR}/client.key"
CLIENT_CSR="${CERT_DIR}/client.csr"
CLIENT_CERT="${CERT_DIR}/client.crt"

echo "Generating certificates for mTLS..."

# Create certs directory
mkdir -p "${CERT_DIR}"

# Generate CA private key
echo "1. Generating CA private key..."
openssl genrsa -out "${CA_KEY}" 4096

# Generate CA certificate
echo "2. Generating CA certificate..."
openssl req -new -x509 -days 3650 -key "${CA_KEY}" -out "${CA_CERT}" \
    -subj "/C=SE/ST=Stockholm/L=Stockholm/O=CopyPaste/OU=Security/CN=CopyPaste-CA"

# Generate server private key
echo "3. Generating server private key..."
openssl genrsa -out "${SERVER_KEY}" 4096

# Generate server CSR
echo "4. Generating server CSR..."
openssl req -new -key "${SERVER_KEY}" -out "${SERVER_CSR}" \
    -subj "/C=SE/ST=Stockholm/L=Stockholm/O=CopyPaste/OU=Server/CN=localhost"

# Generate server certificate signed by CA
echo "5. Generating server certificate..."
openssl x509 -req -days 365 -in "${SERVER_CSR}" -CA "${CA_CERT}" -CAkey "${CA_KEY}" \
    -CAcreateserial -out "${SERVER_CERT}" \
    -extensions v3_req -extfile <(
        echo "[v3_req]"
        echo "keyUsage = keyEncipherment, dataEncipherment"
        echo "extendedKeyUsage = serverAuth"
        echo "subjectAltName = @alt_names"
        echo "[alt_names]"
        echo "DNS.1 = localhost"
        echo "IP.1 = 127.0.0.1"
    )

# Generate client private key
echo "6. Generating client private key..."
openssl genrsa -out "${CLIENT_KEY}" 4096

# Generate client CSR
echo "7. Generating client CSR..."
openssl req -new -key "${CLIENT_KEY}" -out "${CLIENT_CSR}" \
    -subj "/C=SE/ST=Stockholm/L=Stockholm/O=CopyPaste/OU=Client/CN=copy-paste-client"

# Generate client certificate signed by CA
echo "8. Generating client certificate..."
openssl x509 -req -days 365 -in "${CLIENT_CSR}" -CA "${CA_CERT}" -CAkey "${CA_KEY}" \
    -CAcreateserial -out "${CLIENT_CERT}" \
    -extensions v3_req -extfile <(
        echo "[v3_req]"
        echo "keyUsage = digitalSignature, keyEncipherment"
        echo "extendedKeyUsage = clientAuth"
    )

# Clean up CSRs
rm -f "${SERVER_CSR}" "${CLIENT_CSR}"

# Set permissions
chmod 600 "${CA_KEY}" "${SERVER_KEY}" "${CLIENT_KEY}"
chmod 644 "${CA_CERT}" "${SERVER_CERT}" "${CLIENT_CERT}"

echo ""
echo "✅ Certificates generated successfully!"
echo ""
echo "Files created:"
echo "  - CA: ${CA_CERT}"
echo "  - Server: ${SERVER_CERT} (${SERVER_KEY})"
echo "  - Client: ${CLIENT_CERT} (${CLIENT_KEY})"
echo ""
echo "⚠️  Keep these files secure! Add certs/ to .gitignore"
