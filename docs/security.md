# Security - Teknisk Säkerhet

Detta dokument beskriver tekniska säkerhetsåtgärder i Copy/Paste.

## Översikt

Copy/Paste implementerar flera lager av säkerhetsåtgärder för att skydda känsligt journalistiskt material och källor.

## Privacy Guard

### Förbjudna Fält

**Content Protection:**
- `body`, `text`, `content`, `transcript`, `note_body`, `file_content`, `payload`, `query_params`, `query`, `segment_text`, `transcript_text`, `file_data`, `raw_content`, `original_text`

**Source Protection (SOURCE_SAFETY_MODE):**
- `ip`, `client_ip`, `remote_addr`, `x-forwarded-for`, `x-real-ip`
- `user_agent`, `user-agent`
- `referer`, `referrer`, `origin`
- `url`, `uri`
- `filename`, `filepath`, `file_path`, `original_filename`
- `querystring`, `query_string`
- `cookies`, `cookie`
- `headers`, `host`, `hostname`

### Beteende

**DEV Mode (`DEBUG=true`):**
- `AssertionError` vid överträdelser
- Fail-fast för att upptäcka problem tidigt

**PROD Mode (`DEBUG=false`):**
- Droppar förbjudna fält tyst
- Loggar safe warning-event (utan content)
- Fortsätter fungera utan att läcka data

## File Encryption

### Kryptering

- **Algoritm:** Fernet (symmetric encryption)
- **Key:** `PROJECT_FILES_KEY` (base64-encoded, från env)
- **Storage:** Filer sparas som `{sha256}.bin` (ingen originalfilnamn på disk)
- **Content:** Krypterat innan lagring

### Key Management

**Generering:**
```bash
python3 -c "from cryptography.fernet import Fernet; import base64; key = Fernet.generate_key(); print('PROJECT_FILES_KEY=' + base64.b64encode(key).decode('utf-8'))"
```

**Krav:**
- Key måste vara säkert lagrad (secrets manager)
- Rotera regelbundet
- Logga aldrig key

### Secure Delete Policy

**Vad vi garanterar:**
- Filer raderas från filsystemet
- Krypterade blobs tas bort (encrypted content)
- Best-effort overwrite (kan inte garanteras på SSD)

**Vad vi INTE garanterar:**
- Fysisk overwrite på SSD (wear leveling, TRIM)
- Data recovery omöjlighet (kräver disk encryption + kontrollerad storage)

**Vår säkerhetsmodell:**
- Vi litar på **encryption-at-rest** + **deletion of encrypted blobs**
- Om filen är krypterad och blobben är raderad: innehållet är säkert även om fysiska bitar finns kvar
- För riktig garanti: Använd disk encryption (LUKS, BitLocker) + kontrollerad storage

**Implementation:**
- Best-effort overwrite med nollor
- `fsync()` om stöds
- Radera filen
- Dokumentera tydligt vad som garanteras och inte

## Integrity Verification

### Hash Verification

- **Notes:** `note_integrity_hash` (SHA256 av body_text)
- **Transcripts:** `raw_integrity_hash` (SHA256 av raw content)
- **Files:** `sha256` (SHA256 av file content)

### Verification Endpoint

`GET /api/v1/projects/{id}/verify`

Returnerar:
```json
{
  "integrity_ok": true,
  "checked": {
    "transcripts": 3,
    "notes": 2,
    "files": 1
  },
  "issues": []
}
```

## Docker Hardening

### Security Features

- **Non-root user:** `appuser` (uid 1000)
- **Read-only filesystem:** Utom `/app/data`
- **Capabilities dropped:** `cap_drop: ALL`
- **No new privileges:** `no-new-privileges:true`
- **Tmpfs:** `/tmp` och `/var/tmp` som tmpfs

### Network Isolation

- **No egress:** Backend får inte ha internet-egress i produktion
- **Internal networks:** Endast kommunikation inom Docker network
- **Database:** Inte exponerad externt

## Source Safety Mode

### Hard Mode

**I produktion (`DEBUG=false`):**
- `SOURCE_SAFETY_MODE` är ALLTID tvingat till `true`
- Om någon försöker sätta `false` → Boot fails med `ValueError`
- Kan inte stängas av i produktion

**Rationale:**
- Källskydd är obligatoriskt för journalistisk användning
- Fail-fast vid försök att kompromissa säkerhet

## Retention Policy

### Policy as Code

- **Default projects:** `RETENTION_DAYS_DEFAULT` (30 dagar)
- **Sensitive projects:** `RETENTION_DAYS_SENSITIVE` (7 dagar)
- **Temp files:** `TEMP_FILE_TTL_HOURS` (24 timmar)

### Cleanup

- **Script:** `scripts/cleanup_retention.py`
- **Frequency:** Kör regelbundet (cron/kubernetes job)
- **Audit:** Loggar `system_cleanup_run` (utan content)

## Error Handling

### Consistent Error Shape

Alla errors returnerar:
```json
{
  "error": {
    "code": "error_code",
    "message": "Generic message",
    "request_id": "uuid-here"
  }
}
```

**Beteende:**
- `DEBUG=false`: Generic message (ingen intern info)
- `DEBUG=true`: Kan inkludera korta, säkra detaljer
- Alltid `request_id` för spårbarhet

## Security Headers

### Response Headers

Alla responses inkluderar:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Cache-Control: no-store`

## CI Security Toolchain

### Automated Checks

- **Bandit:** Python security scanning
- **pip-audit:** Dependency vulnerability scanning
- **Gitleaks:** Secrets detection
- **Trivy:** Container image scanning

**Fail Policy:**
- High/Critical findings → Build fails
- Medium findings → Warnings

## Threat Model

Se `docs/threat-model.md` för detaljerad threat analysis.

## Best Practices

### Development

- Använd `DEBUG=true` för utveckling
- Testa med `SOURCE_SAFETY_MODE=false` för att verifiera guards
- Kör `make verify` regelbundet

### Production

- `DEBUG=false` (hard requirement)
- `SOURCE_SAFETY_MODE=true` (forced)
- Ingen internet-egress för backend
- Read-only filesystem
- Non-root user
- Regular cleanup runs

## Support

För frågor om säkerhet:
- Se `docs/journalism-safety.md` för källskydd
- Se `docs/opsec.md` för operativa säkerhetsrutiner
- Se `docs/user-safety.md` för användarsäkerhet
- Kontakta IT-säkerhetsteamet

