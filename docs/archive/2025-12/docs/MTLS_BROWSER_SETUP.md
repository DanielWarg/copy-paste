<!--
ARCHIVED DOCUMENT
This file is no longer authoritative.
Canonical source of truth: docs/canonical/
-->

# mTLS Browser Setup Guide

## Översikt

För att använda UI:t i browsern med mTLS (mutual TLS) krävs att client-certifikatet installeras i systemets certifikatarkiv och/eller browsern.

## macOS Setup

### 1. Installera Client Certifikat i Keychain

```bash
# Importera client certifikat till macOS Keychain
security import certs/client.crt -k ~/Library/Keychains/login.keychain-db -T /usr/bin/security

# Importera client key (om separat fil)
security import certs/client.key -k ~/Library/Keychains/login.keychain-db -T /usr/bin/security

# Verifiera att certifikatet är installerat
security find-certificate -c "client" ~/Library/Keychains/login.keychain-db
```

### 2. Konfigurera Browsern

#### Chrome/Edge (Chromium)

1. Öppna `chrome://settings/certificates` (eller `edge://settings/certificates`)
2. Gå till fliken "Your certificates"
3. Klicka "Import" och välj `certs/client.crt`
4. Ange lösenord om det krävs
5. Starta om browsern

**Verifiering:**
- Öppna `https://localhost` i browsern
- Om certifikatet är korrekt installerat kommer browsern automatiskt att använda det för mTLS
- Om certifikatet saknas kommer TLS handshake att misslyckas (ingen 403, utan connection error)

#### Firefox

Firefox använder sitt eget certifikatarkiv:

1. Öppna Firefox Preferences → Privacy & Security → Certificates
2. Klicka "View Certificates" → "Your Certificates"
3. Klicka "Import" och välj `certs/client.crt`
4. Ange lösenord om det krävs

**Verifiering:**
- Öppna `https://localhost` i Firefox
- Om certifikatet saknas kommer TLS handshake att misslyckas

#### Safari

Safari använder systemets Keychain:

1. Öppna Keychain Access (Sök efter "Keychain Access" i Spotlight)
2. Hitta certifikatet "client" (eller det namn du gav det)
3. Dubbelklicka och verifiera att det är "trusted"
4. Om det inte är trusted: Högerklicka → "Get Info" → Expandera "Trust" → Sätt "When using this certificate" till "Always Trust"

**Verifiering:**
- Öppna `https://localhost` i Safari
- Om certifikatet saknas kommer TLS handshake att misslyckas

### 3. Testa mTLS i Browsern

#### Med Certifikat (förväntat: 200 OK)

```bash
# Öppna i browsern:
https://localhost/api/v1/projects

# Förväntat resultat:
# - Browsern använder automatiskt client certifikat
# - Request lyckas (200 OK)
# - Response innehåller data
```

#### Utan Certifikat (förväntat: TLS Handshake Fail)

Om certifikatet inte är installerat:

```bash
# Öppna i browsern:
https://localhost/api/v1/projects

# Förväntat resultat:
# - TLS handshake misslyckas
# - Browsern visar "ERR_SSL_CLIENT_AUTH_CERT_NEEDED" eller liknande
# - Ingen 403, utan connection error
```

### 4. UI Error Handling

Om mTLS handshake misslyckas kommer UI:t att visa:

```
❌ Anslutning misslyckades: TLS handshake failed
   Installera client certifikat för att fortsätta.
   
   Se: docs/MTLS_BROWSER_SETUP.md
```

**Brutal-safe:** Inga payloads, inga stack traces, bara error code + request_id (om tillgängligt).

## Linux Setup

### 1. Installera Certifikat

```bash
# Kopiera certifikat till systemets certifikatarkiv
sudo cp certs/client.crt /usr/local/share/ca-certificates/client.crt
sudo update-ca-certificates

# För browsern (Chrome/Chromium):
# Certifikatet måste importeras via browser settings (se Chrome/Edge ovan)
```

### 2. Testa mTLS

Samma som macOS - använd browser settings för att importera certifikatet.

## Windows Setup

### 1. Installera Certifikat i Windows Certificate Store

```powershell
# Importera client certifikat
Import-Certificate -FilePath certs\client.crt -CertStoreLocation Cert:\CurrentUser\My

# Verifiera
Get-ChildItem Cert:\CurrentUser\My | Where-Object {$_.Subject -like "*client*"}
```

### 2. Konfigurera Browsern

Chrome/Edge på Windows använder Windows Certificate Store automatiskt. Firefox kräver manuell import (se Firefox ovan).

## Verifiering

### Automatisk Verifiering (Playwright)

Playwright kan konfigureras för att använda client certifikat:

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    // För mTLS med self-signed certs
    ignoreHTTPSErrors: true,
    // Client certifikat (om Playwright stödjer det)
    // Note: Playwright stödjer inte direkt client certs, så vi använder test-proxy istället
  },
});
```

### Manuell Verifiering

1. Öppna Developer Tools (F12)
2. Gå till Network-tab
3. Försök ladda `https://localhost/api/v1/projects`
4. **Med cert:** Request lyckas (200 OK)
5. **Utan cert:** Request misslyckas (TLS handshake error, ingen 403)

## Troubleshooting

### Problem: "ERR_SSL_CLIENT_AUTH_CERT_NEEDED"

**Lösning:** Installera client certifikat (se ovan)

### Problem: "Certificate not trusted"

**Lösning:** 
- macOS: Sätt certifikatet till "Always Trust" i Keychain Access
- Linux: Verifiera att CA-certifikatet är installerat
- Windows: Verifiera att certifikatet är i "Trusted Root Certification Authorities"

### Problem: Browsern frågar inte efter certifikat

**Lösning:**
- Verifiera att server-certifikatet är korrekt konfigurerat i Caddy
- Verifiera att `client_auth { mode require_and_verify }` är satt i Caddyfile
- Kontrollera att browsern faktiskt ansluter till `https://localhost` (inte `http://`)

## Security Notes

- **Client certifikat är känsliga:** Skydda `certs/client.key` med rättigheter (chmod 600)
- **Inte för produktion:** Self-signed certifikat är endast för utveckling/testning
- **Prod setup:** Använd riktiga CA-utfärdade certifikat i produktion


