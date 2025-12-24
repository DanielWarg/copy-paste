# Säkerhetsmoduler - Komplett Dokumentation

Detta dokument beskriver alla säkerhetsmoduler i Copy/Paste-systemet. Dessa moduler arbetar tillsammans för att skydda källor, förhindra data-läckor och säkerställa journalistisk etik.

## Innehållsförteckning

1. [Privacy Guard](#privacy-guard)
2. [Source Safety Mode](#source-safety-mode)
3. [File Encryption](#file-encryption)
4. [Integrity Verification](#integrity-verification)
5. [Autonomy Guard](#autonomy-guard)
6. [Retention & Cleanup](#retention--cleanup)
7. [Egress Control](#egress-control)

---

## Privacy Guard

**Fil:** `backend/app/core/privacy_guard.py`

**Syfte:** Förhindra att innehåll och källidentifierare hamnar i logs eller audit trails.

### Förbjudna Fält

**Content Protection:**
- `body`, `text`, `content`, `transcript`, `note_body`, `file_content`
- `payload`, `query_params`, `query`
- `segment_text`, `transcript_text`, `file_data`, `raw_content`, `original_text`

**Source Protection (SOURCE_SAFETY_MODE):**
- `ip`, `client_ip`, `remote_addr`, `x-forwarded-for`, `x-real-ip`
- `user_agent`, `user-agent`
- `referer`, `referrer`, `origin`
- `url`, `uri`
- `filename`, `filepath`, `file_path`, `original_filename`
- `querystring`, `query_string`
- `cookies`, `cookie`
- `headers`, `host`, `hostname`

### Funktioner

#### `sanitize_for_logging(data, context)`

Sanitizerar data för logging/audit.

**Beteende:**
- DEV mode (`DEBUG=true`): `AssertionError` vid överträdelser
- PROD mode (`DEBUG=false`): Droppar förbjudna fält tyst + loggar safe warning

**Exempel:**
```python
from app.core.privacy_guard import sanitize_for_logging

# Försöker logga med förbjudna fält
data = {
    "action": "file_uploaded",
    "ip": "192.168.1.1",  # Förbjudet
    "filename": "source.pdf",  # Förbjudet
    "count": 1,  # OK
}

# DEV mode: AssertionError
# PROD mode: Droppar ip och filename, behåller action och count
sanitized = sanitize_for_logging(data, context="audit")
```

#### `assert_no_content(data, context)`

Strikt kontroll att data inte innehåller förbjudna fält.

**Beteende:**
- Alltid `AssertionError` vid överträdelser (både DEV och PROD)

**Användning:**
```python
from app.core.privacy_guard import assert_no_content

# Verifiera audit event innan sparning
audit_data = {
    "action": "exported",
    "format": "srt",
    "count": 42,
}
assert_no_content(audit_data, context="audit")  # OK

# Failar om förbjudna fält finns
bad_data = {"action": "exported", "transcript_text": "..."}
assert_no_content(bad_data, context="audit")  # AssertionError
```

#### `compute_integrity_hash(content)`

Beräknar SHA256 hash för integritetsverifiering.

**Användning:**
```python
from app.core.privacy_guard import compute_integrity_hash

hash_value = compute_integrity_hash("Detta är innehållet")
# Returnerar: SHA256 hex digest
```

#### `verify_integrity(content, expected_hash)`

Verifierar innehåll mot förväntad hash.

**Användning:**
```python
from app.core.privacy_guard import verify_integrity

is_valid = verify_integrity("Detta är innehållet", expected_hash)
# Returnerar: True om hash matchar, False annars
```

### Integration

Privacy Guard används automatiskt av:
- `app.core.logging` - Filtrerar log-data
- `app.modules.transcripts.router` - Sanitizerar audit events
- `app.modules.projects` - Sanitizerar projekt-audit events

---

## Source Safety Mode

**Fil:** `backend/app/core/config.py`

**Syfte:** Tvinga källskydd i produktion - kan inte stängas av.

### Konfiguration

**Environment Variable:** `SOURCE_SAFETY_MODE=true|false`

**Default:** `true`

**Hard Mode:** I produktion (`DEBUG=false`) är `SOURCE_SAFETY_MODE` ALLTID tvingat till `true`.

### Beteende

**Development (`DEBUG=true`):**
- `SOURCE_SAFETY_MODE` kan stängas av för testning
- Privacy Guard blockerar källidentifierare med `AssertionError`

**Production (`DEBUG=false`):**
- `SOURCE_SAFETY_MODE` är ALLTID `true` (tvingat)
- Om någon försöker sätta `false` → Boot fails med `ValueError`
- Ytterligare fält förbjuds i logs/audit

### Validering

```python
# I config.py model_post_init:
if not self.debug and not self.source_safety_mode:
    raise ValueError(
        "SOURCE_SAFETY_MODE cannot be False in production (DEBUG=false). "
        "Source protection is mandatory for newsroom operations."
    )

# Tvinga till True i produktion
if not self.debug:
    self.source_safety_mode = True
```

### Verifiering

```bash
# Testa att boot failar om SOURCE_SAFETY_MODE=false i prod
DEBUG=false SOURCE_SAFETY_MODE=false python -c "from app.core.config import settings"
# Förväntat: ValueError
```

---

## File Encryption

**Fil:** `backend/app/modules/projects/file_storage.py`

**Syfte:** Kryptera filer innan lagring på disk.

### Kryptering

**Algoritm:** Fernet (symmetric encryption)

**Key:** `PROJECT_FILES_KEY` (base64-encoded, från environment)

**Storage Format:** Filer sparas som `{sha256}.bin` (ingen originalfilnamn på disk)

### Funktioner

#### `compute_file_hash(content)`

Beräknar SHA256 hash av file content.

```python
from app.modules.projects.file_storage import compute_file_hash

hash_value = compute_file_hash(file_bytes)
# Returnerar: SHA256 hex digest
```

#### `encrypt_content(content)`

Krypterar file content.

```python
from app.modules.projects.file_storage import encrypt_content

encrypted = encrypt_content(file_bytes)
# Returnerar: Encrypted bytes
```

#### `decrypt_content(encrypted_content)`

Dekrypterar file content.

```python
from app.modules.projects.file_storage import decrypt_content

decrypted = decrypt_content(encrypted_bytes)
# Returnerar: Decrypted bytes
```

#### `store_file(content, sha256)`

Lagrar krypterad fil på disk.

**Process:**
1. Verifierar att hash matchar content
2. Krypterar content
3. Sparar som `{sha256}.bin` i `/app/data/files`
4. Returnerar storage path

```python
from app.modules.projects.file_storage import store_file

storage_path = store_file(file_bytes, sha256_hash)
# Returnerar: "{sha256}.bin"
```

#### `retrieve_file(sha256)`

Hämtar och dekrypterar fil från disk.

```python
from app.modules.projects.file_storage import retrieve_file

content = retrieve_file(sha256_hash)
# Returnerar: Decrypted file bytes
```

#### `delete_file(sha256)`

Raderar fil från disk (secure deletion).

**Process:**
1. Överskriver med nollor (best effort)
2. Raderar filen

```python
from app.modules.projects.file_storage import delete_file

delete_file(sha256_hash)
```

#### `generate_encryption_key()`

Genererar ny Fernet encryption key (för setup).

```python
from app.modules.projects.file_storage import generate_encryption_key

key_b64 = generate_encryption_key()
# Returnerar: Base64-encoded Fernet key
# Använd i: PROJECT_FILES_KEY environment variable
```

### Key Management

**Generering:**
```bash
python3 -c "from app.modules.projects.file_storage import generate_encryption_key; print('PROJECT_FILES_KEY=' + generate_encryption_key())"
```

**Krav:**
- Key måste vara säkert lagrad (secrets manager)
- Rotera regelbundet
- Logga aldrig key

**Setup:**
```bash
# .env
PROJECT_FILES_KEY=<base64-encoded-fernet-key>
```

### Storage Structure

```
/app/data/files/
  ├── {sha2561}.bin  # Encrypted file 1
  ├── {sha2562}.bin  # Encrypted file 2
  └── ...
```

**Viktigt:**
- Ingen originalfilnamn på disk
- Alla filer krypterade
- SHA256 används som identifierare

---

## Integrity Verification

**Fil:** `backend/app/modules/projects/integrity.py`

**Syfte:** Verifiera integritet för alla artefakter i ett projekt.

### Funktioner

#### `verify_project_integrity(project_id)`

Verifierar integritet för alla artefakter i ett projekt.

**Process:**
1. Verifierar notes (hash matchar body_text)
2. Verifierar transcripts (hash matchar raw content om satt)
3. Verifierar files (filer finns på disk)

**Returnerar:**
```python
{
    "integrity_ok": True,
    "checked": {
        "transcripts": 3,
        "notes": 2,
        "files": 1
    },
    "issues": []
}
```

**Exempel:**
```python
from app.modules.projects.integrity import verify_project_integrity

result = verify_project_integrity(project_id=1)
if not result["integrity_ok"]:
    print(f"Integrity issues: {result['issues']}")
```

### Hash Verification

**Notes:**
- `note_integrity_hash` = SHA256 av `body_text`
- Verifieras vid integrity check

**Transcripts:**
- `raw_integrity_hash` = SHA256 av raw transcript content (alla segments)
- Verifieras vid integrity check (om hash är satt)

**Files:**
- `sha256` = SHA256 av file content
- Verifieras att fil finns på disk

### API Endpoint

**GET** `/api/v1/projects/{id}/verify`

**Response:**
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

**Användning:**
- Verifiera att material inte korrupterats
- Kontrollera att filer finns på disk
- Verifiera hash-integrity för notes och transcripts

---

## Autonomy Guard

**Fil:** `backend/app/modules/autonomy_guard/checks.py`

**Syfte:** Regelbaserade checks för att flagga potentiella problem (NO AI).

### Checks

#### 1. Unusually Short Transcript

**Regel:** Transcript med < 100 tecken flaggas.

**Severity:** `warning`

**Message:** "Transcript 'X' är ovanligt kort (N tecken)."

**Why:** "Korta transkriptioner kan tyda på ofullständig data eller tekniskt fel."

#### 2. Low Average Confidence

**Regel:** Transcript med genomsnittlig confidence < 70% flaggas.

**Severity:** `warning`

**Message:** "Transcript 'X' har låg genomsnittlig konfidens (N%)."

**Why:** "Låg konfidens kan tyda på dålig ljudkvalitet eller transkriptionsfel."

#### 3. Rapid Deletion Activity

**Regel:** > 3 raderingar under senaste timmen flaggas.

**Severity:** `warning`

**Message:** "Ovanligt många raderingar (N) under senaste timmen."

**Why:** "Rapid deletion activity kan tyda på misstag eller säkerhetsproblem."

#### 4. Sensitive Project with Retained Files

**Regel:** Sensitive projekt med filer kvar flaggas.

**Severity:** `warning`

**Message:** "Detta projekt innehåller känsligt material som fortfarande sparas."

**Why:** "Projektet är markerat som känsligt och filer är kvar. Överväg att arkivera eller radera när arbetet är klart."

#### 5. Inactive Project with Content

**Regel:** Arkiverat projekt med innehåll, inaktivt > 90 dagar flaggas.

**Severity:** `info`

**Message:** "Arkiverat projekt med innehåll (N artefakter) har varit inaktivt i N dagar."

**Why:** "Överväg att radera innehåll om det inte längre behövs."

### Funktioner

#### `check_project(project_id)`

Kör alla autonomy checks för ett projekt.

**Returnerar:**
```python
[
    {
        "severity": "warning",
        "message": "Detta projekt innehåller känsligt material...",
        "why": "Projektet är markerat som känsligt..."
    },
    # ... fler checks
]
```

**Användning:**
```python
from app.modules.autonomy_guard.checks import check_project

checks = check_project(project_id=1)
for check in checks:
    print(f"{check['severity']}: {check['message']}")
    print(f"  Why: {check['why']}")
```

#### `flag_project(project_id, checks, request_id)`

Skapar audit events för autonomy guard flags.

**Process:**
1. Skapar `ProjectAuditEvent` för varje check
2. Action: `system_flag`
3. Severity: från check (info|warning|critical)
4. Metadata: message + why (utan content)

**Användning:**
```python
from app.modules.autonomy_guard.checks import check_project, flag_project

checks = check_project(project_id=1)
if checks:
    flag_project(project_id=1, checks=checks, request_id="abc-123")
```

### Viktiga Principer

**NO AI:**
- Alla checks är regelbaserade (deterministiska)
- Inga LLM-anrop eller AI-beslut

**Non-Blocking:**
- Checks flaggar endast problem
- Blockar ALDRIG handlingar
- Användaren har alltid sista ordet

**Audit Trail:**
- Alla flags loggas i audit (utan content)
- Spårbarhet för granskning

---

## Retention & Cleanup

**Fil:** `scripts/cleanup_retention.py`

**Syfte:** Rensa gamla filer och projekt enligt retention policy.

### Policy

**Settings:**
- `RETENTION_DAYS_DEFAULT=30` (default projects)
- `RETENTION_DAYS_SENSITIVE=7` (sensitive projects)
- `TEMP_FILE_TTL_HOURS=24` (temp files)

### Funktioner

#### `cleanup_retention()`

Kör retention cleanup enligt policy.

**Process:**
1. Rensar temp files äldre än TTL
2. Rensar destroyed projects äldre än retention
3. Sensitive projects: kortare retention
4. Skapar audit event `system_cleanup_run` (utan content)

**Returnerar:**
```python
{
    "status": "success",
    "counts": {
        "temp_files_deleted": 5,
        "destroyed_projects_deleted": 2,
        "sensitive_projects_deleted": 1,
        "errors": 0
    }
}
```

### Användning

**Manuellt:**
```bash
python3 scripts/cleanup_retention.py
```

**Cron/Job:**
```bash
# Kör dagligen kl 02:00
0 2 * * * cd /app && python3 scripts/cleanup_retention.py
```

### Audit Logging

Cleanup runs loggas som:
```json
{
  "action": "system_cleanup_run",
  "severity": "info",
  "actor": "system",
  "metadata_json": {
    "temp_files_deleted": 5,
    "destroyed_projects_deleted": 2,
    "sensitive_projects_deleted": 1,
    "errors": 0
  }
}
```

**Viktigt:** Metadata innehåller endast counts, aldrig content eller identifiers.

---

## Egress Control

**Fil:** `scripts/check_egress.py`

**Syfte:** Verifiera att backend inte kan nå externa endpoints (produktionskrav).

### Funktioner

#### `check_egress()`

Kontrollerar om backend kan nå externa endpoints.

**Test Endpoints:**
- `example.com:80`
- `8.8.8.8:53` (Google DNS)

**Returnerar:**
```python
{
    "can_reach_external": False,
    "endpoints_tested": [
        {"host": "example.com", "port": 80, "reachable": False}
    ],
    "status": "PASS",  # eller "FAIL" eller "INFO"
    "message": "Backend cannot reach external endpoints (as required in production)"
}
```

### Beteende

**Production (`DEBUG=false`):**
- Förväntat: `can_reach_external = False`
- Om `True` → Status: `FAIL` (security issue)

**Development (`DEBUG=true`):**
- Status: `INFO` (informational only)
- Egress tillåten för utveckling

### Användning

**Manuellt:**
```bash
python3 scripts/check_egress.py
```

**CI/CD:**
```bash
# Kör vid deployment
python3 scripts/check_egress.py || exit 1
```

### Implementation i Produktion

**Docker:**
- Använd `--network none` eller begränsa till intern nätverk
- NetworkPolicy för att blockera egress

**Kubernetes:**
- NetworkPolicy för att blockera egress
- Verifiera med `check_egress.py`

**Cloud:**
- Security groups/firewall rules
- Verifiera med `check_egress.py`

---

## Integration

### Hur Modulerna Arbetar Tillsammans

```
Request → Privacy Guard → Source Safety Mode → Logging
                ↓
         Audit Event (sanitized)
                ↓
         Autonomy Guard (checks)
                ↓
         Flag (if needed)
```

**Exempel Flow:**

1. **Request kommer in**
   - Middleware loggar (Privacy Guard filtrerar)
   - Source Safety Mode blockerar källidentifierare

2. **File upload**
   - File Encryption krypterar fil
   - Integrity hash beräknas
   - Storage path: `{sha256}.bin`

3. **Audit event**
   - Privacy Guard sanitizerar metadata
   - Source Safety Mode blockerar filnamn/IP
   - Event sparas (utan content)

4. **Autonomy Guard**
   - Kör regelbaserade checks
   - Flaggar potentiella problem
   - Skapar audit events (utan content)

5. **Retention Cleanup**
   - Rensar gamla filer/projekt
   - Loggar cleanup run (counts only)

### Verifiering

**Kör alla säkerhetsverifieringar:**
```bash
# Source Safety Mode
python3 scripts/test_source_safety.py

# Security Freeze
python3 scripts/test_security_freeze.py

# Log Hygiene
python3 scripts/check_logs.py

# Egress Check
python3 scripts/check_egress.py

# Complete Verification
make verify
```

---

## Best Practices

### Development

- Använd `DEBUG=true` för utveckling
- Testa med `SOURCE_SAFETY_MODE=false` för att verifiera guards
- Kör `make verify` regelbundet

### Production

- `DEBUG=false` (hard requirement)
- `SOURCE_SAFETY_MODE=true` (forced)
- Ingen internet-egress för backend
- Regular cleanup runs
- Integrity verification regelbundet

### Monitoring

**Daglig:**
- Egress check
- Log hygiene check
- Retention cleanup

**Veckovis:**
- Integrity verification
- Security audit review

**Månadsvis:**
- Full security audit
- Policy review

---

## Support

För frågor om säkerhetsmoduler:
- Se `docs/journalism-safety.md` för källskydd
- Se `docs/security.md` för tekniska säkerhetsdetaljer
- Se `docs/opsec.md` för operativa säkerhetsrutiner
- Kontakta IT-säkerhetsteamet

