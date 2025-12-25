# Copy/Paste - Komplett Säkerhetsdokumentation

**Senast uppdaterad:** 2025-12-25  
**Version:** 1.0.0  
**Status:** Production Ready

---

## Innehållsförteckning

1. [Executive Summary](#executive-summary)
2. [Säkerhetsgarantier](#säkerhetsgarantier)
3. [Säkerhetsarkitektur](#säkerhetsarkitektur)
4. [Threat Model](#threat-model)
5. [Säkerhetsmoduler](#säkerhetsmoduler)
6. [Operational Security](#operational-security)
7. [Journalism Safety & Källskydd](#journalism-safety--källskydd)
8. [User Safety](#user-safety)
9. [Privacy Gate](#privacy-gate)
10. [Certificate Lifecycle](#certificate-lifecycle)
11. [Incident Response](#incident-response)
12. [Verification & Testing](#verification--testing)
13. [Risk Assessment](#risk-assessment)
14. [Compliance & Regulatory](#compliance--regulatory)

---

## Executive Summary

Copy/Paste är ett journalistiskt AI-assistanssystem med fokus på källskydd, dataskydd och integritet. Systemet implementerar "Brutal Security Profile v3.1" som garanterar zero egress, mTLS enforcement, Privacy Gate, och fail-closed design.

### Vad systemet skyddar

**Journalistiskt material:**
- Källkontakter och råmaterial från källor
- Transkriptioner av känsliga samtal
- Artiklar under utveckling
- Personuppgifter som måste skyddas enligt GDPR

**Säkerhetsgarantier:**
- Zero egress: Backend kan inte nå internet (infrastruktur + kod-nivå)
- mTLS enforcement: All extern åtkomst över HTTPS kräver klientcertifikat (mTLS). Drift-health/readiness sker över HTTP.
- Privacy Gate: Ingen rå PII skickas till externa AI:er
- Fail-closed design: Systemet startar inte i osäkert läge

### Vad systemet inte gör i prod_brutal (enforced by design)

**Systemet kan inte skicka data till internet (i prod_brutal runtime):**
- I prod_brutal runtime är backend placerad på ett Docker-internal network (`internal_net: internal: true`) utan egress och saknar routning till internet
- Blockerat både på nätverksnivå (Docker network isolation) och på kodnivå (`ensure_egress_allowed()` blockerar i prod_brutal)
- För att bryta detta krävs administrativ åtkomst och ändring av driftkonfiguration (docker-compose, network settings)

**Systemet kräver mTLS för all extern åtkomst över HTTPS:**
- All extern åtkomst över HTTPS (port 443) kräver giltigt klientcertifikat (`client_auth require_and_verify`)
- Health/readiness endpoints är endast tillgängliga via intern/host-åtkomst över HTTP (port 80) och används för drift, inte användartrafik
- Det finns ingen "lösenordsinloggning" eller "återställ lösenord"-funktion för användartrafik

**Systemet kan inte skicka rå text till externa AI:er:**
- All text måste först passera "Privacy Gate" som maskerar personlig information
- Om systemet upptäcker personuppgifter efter maskningen, blockeras hela förfrågan
- Det finns ingen väg runt detta

**Systemet kan inte starta i osäkert läge:**
- Om systemet inte kan garantera säkerheten vid start, startar det inte alls
- Hellre nere än osäkert

**Systemet kan inte logga känslig data:**
- Alla loggar är designade för att aldrig innehålla personuppgifter, lösenord, nycklar eller innehåll
- Om något skulle gå fel loggas bara vad som gick fel (feltyp), inte vad som faktiskt hände

---

## Säkerhetsgarantier

### Guarantee 1: Zero Egress

**Infrastructure Level:**
- `internal_net: internal: true` → Ingen gateway, ingen egress
- I prod_brutal runtime kan backend inte nå internet via Docker network (ingen routning till gateway)
- För att bryta detta krävs administrativ åtkomst och ändring av driftkonfiguration

**Code Level:**
- `ensure_egress_allowed()` blockerar egress i `prod_brutal` profile (raise `EgressBlockedError`)
- Alla externa providers måste kalla `ensure_egress_allowed()` innan network requests
- Startup check: Boot fail om cloud API keys (t.ex. `OPENAI_API_KEY`) är satta i env i prod_brutal (nyckeln är optional men förbjuden om satt)

**Verification:**
- `scripts/verify_no_internet.sh` (runtime verification)
- `make verify-brutal` (full verification)

### Guarantee 2: mTLS Enforcement

**Proxy Level:**
- `client_auth require_and_verify` i Caddyfile (port 443)
- Alla HTTPS-requests kräver giltigt klientcertifikat (TLS handshake fail utan cert)
- Health/readiness endpoints är tillgängliga via HTTP (port 80) utan mTLS för driftmonitoring
- Certificate revocation support (CRL) är planerad men inte aktivt konfigurerad i nuvarande setup

**Verification:**
- `scripts/verify_mtls.sh` (TLS handshake fail utan cert, 200 med cert)
- `make verify-brutal` (full verification)

### Guarantee 3: Privacy Gate

**Type-Safe Enforcement:**
- `MaskedPayload` är enda tillåtna input för externa LLM providers
- Privacy Gate är obligatorisk (`privacy_gate.ensure_masked_or_raise()`)
- Inget raw text kan nå externa AI:er utan att passera Privacy Gate

**Multi-Pass Masking:**
- Pass 1: Initial masking
- Pass 2: Re-mask on result (catches overlaps, edge cases)
- Pass 3 (strict mode): One more pass for maximum safety

**Fail-Closed Leak Check:**
- ANY detected PII = BLOCK (422)
- No compromise, no fallback

**Verification:**
- `make verify-privacy-chain` (privacy chain verification)
- Privacy Shield leak prevention tests (se `tests/results/` för testrapporter)

### Guarantee 4: Fail-Closed Design

**Boot Fail Policy:**
- Systemet startar inte om secrets saknas i `prod_brutal` (t.ex. `fernet_key` måste finnas i `/run/secrets/`)
- Systemet startar inte om cloud API keys (t.ex. `OPENAI_API_KEY`) är satta i env i prod_brutal (nyckeln är optional men förbjuden om satt - fail-closed)
- Systemet startar inte om osäker konfiguration (t.ex. `SOURCE_SAFETY_MODE=false` i produktion)

**Runtime Fail-Closed:**
- Privacy Gate blockerar PII (422, ingen draft genereras)
- Egress guard blockerar externa requests (exception)
- mTLS blockerar unauthorized access (TLS handshake fails utan giltigt cert)

**Verification:**
- Startup checks (boot fail verification)
- Runtime checks (egress guard, Privacy Gate)

### Guarantee 5: Secret Management

**Docker Secrets:**
- I `prod_brutal` profile MÅSTE secrets komma från `/run/secrets/`
- Backend läser secrets från `/run/secrets/` (fallback till env endast i dev)
- Boot fail om secret saknas i `prod_brutal`

**Key Management:**
- `PROJECT_FILES_KEY` från säker secrets manager
- Rotera regelbundet
- Logga aldrig secrets

---

## Säkerhetsarkitektur

### Network Architecture

**Topology:**
```
Internet
   │
   │ (HTTPS + mTLS)
   ▼
[Proxy (Caddy)]
   │
   │ (HTTP over internal_net)
   ▼
[Backend]
   │
   │ (NO egress - internal_net is internal: true)
   └─→ BLOCKED
```

**Components:**
- **Proxy (Caddy):** Exponerar port 443/80, enforcerar mTLS, proxyar till backend
- **Backend:** Ingen port exponerad till host, ansluten endast till internal_net
- **Internal Network:** `internal: true` → Ingen gateway, ingen egress

**Security Hardening:**
- Backend: `read_only: true`, `cap_drop: ALL`, non-root user, `tmpfs` för /tmp
- Proxy: mTLS enforcement (`client_auth require_and_verify`)

### Privacy Architecture

**Privacy Gate:**
- Obligatorisk maskning via `privacy_gate.ensure_masked_or_raise()`
- Multi-pass masking (2-3 pass beroende på mode)
- Fail-closed leak check (ANY detected PII = BLOCK 422)
- Type-safe enforcement (`MaskedPayload` är enda tillåtna input för externa providers)

**Privacy Shield:**
- Baseline regex masking (email, phone, PNR, etc.)
- Leak check (blockerande preflight)
- Control model (advisory, strict mode)
- External LLM egress hard gate (endast `MaskedPayload`)

**Verification:**
- Privacy chain test (`make verify-privacy-chain`)
- Privacy Shield leak prevention tests (se `tests/results/` för testrapporter)
- CI enforcement (`make check-privacy-gate`)

### Access Control Architecture

**mTLS Certificate → User Role Mapping:**
- Certifikat innehåller metadata (CN, O, OU) som mappas till roller
- Proxy validerar mTLS-certifikat och extraherar roll
- Backend är auth-agnostisk men kan läsa `X-User-Role` för audit

**Certificate Lifecycle:**
- Create: Admin genererar certifikat via `scripts/cert_create.sh`, signeras av CA, distribueras säkert
- Rotate: Före utgång, nytt cert distribueras via `scripts/cert_rotate.sh`, gammalt cert revokeras
- Revoke: Omedelbar revokering vid kompromittering via `scripts/cert_revoke.sh` (CRL support planerad)
- Emergency Disable: Break-glass-procedure via `scripts/cert_emergency_disable.sh` för kritiska incidenter

---

## Threat Model

### Threat 1: Källidentifiering

**Hot:** Attacker eller myndigheter försöker identifiera källor genom metadata.

**Skydd:**
- Inga IP-adresser i logs/audit
- Inga filnamn i logs/audit
- Inga URLs i logs/audit
- Inga user-agents i logs/audit
- SOURCE_SAFETY_MODE forced i produktion

**Verifiering:**
- `scripts/test_source_safety.py` (verifierar source protection)
- Privacy Guard enforcement (automatisk i produktion via `source_safety_mode=true`)
- `make verify` (kör verifieringar)

### Threat 2: Content Leakage

**Hot:** Känsligt innehåll läcker i logs, audit trails eller felmeddelanden.

**Skydd:**
- Privacy Guard blockerar content-fält
- Audit trails innehåller endast metadata (counts, ids, format)
- Error messages är generiska i produktion
- Inga stack traces i produktion

**Verifiering:**
- `scripts/test_source_safety.py` (verifierar content blocking)
- Privacy Guard enforcement (automatisk blocking av content-fält i produktion)
- Manual log review (verifiera att inga content-fält läcker)

### Threat 3: Data Exfiltration

**Hot:** Attacker försöker stjäla känsligt material.

**Skydd:**
- Ingen internet-egress för backend i produktion
- File encryption (Fernet)
- Filer sparas som `{sha256}.bin` (ingen originalfilnamn)
- Read-only filesystem (utom `/app/data`)

**Verifiering:**
- `scripts/check_egress.py` (verifierar egress blocking)
- `scripts/verify_no_internet.sh` (runtime verification)
- Network isolation checks (docker network config)
- File encryption verification

### Threat 4: Unauthorized Access

**Hot:** Obefintlig användare får tillgång till systemet.

**Skydd:**
- mTLS enforcement (client certificate required för HTTPS)
- No public backend ports (backend endast på internal_net)
- Internal network isolation (`internal_net: internal: true`)
- Certificate revocation support (CRL planerad, scripts finns: `cert_revoke.sh`)

**Verifiering:**
- `scripts/verify_mtls.sh` (mTLS verification - TLS handshake fail utan cert, 200 med cert)
- `make verify-brutal` (full verification)

### Threat 5: PII Leakage to External AI

**Hot:** Personuppgifter skickas till externa AI-tjänster.

**Mitigation:**
- Privacy Gate (obligatory masking)
- Multi-pass masking (edge cases caught)
- Fail-closed leak check (ANY detected PII = BLOCK)
- Type-safe enforcement (`MaskedPayload`)

**Verification:**
- `make verify-privacy-chain` (privacy chain verification)
- Privacy Shield leak prevention tests (se `tests/results/` för testrapporter)

### Threat 6: Misconfiguration

**Hot:** Osäker konfiguration gör systemet sårbart.

**Mitigation:**
- Boot fail if secrets missing
- Boot fail if cloud keys present
- Static validation scripts
- Runtime validation scripts

**Verification:**
- `scripts/validate_del_a.sh` (static validation av docker-compose och Caddyfile)
- `make verify-brutal` (full verification)

---

## Säkerhetsmoduler

### Privacy Guard

**Fil:** `backend/app/core/privacy_guard.py`

**Syfte:** Förhindra att innehåll och källidentifierare hamnar i logs eller audit trails.

**Förbjudna Fält:**

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

**Beteende:**
- DEV mode (`DEBUG=true`): `AssertionError` vid överträdelser
- PROD mode (`DEBUG=false`): Droppar förbjudna fält tyst + loggar safe warning

### Source Safety Mode

**Fil:** `backend/app/core/config.py`

**Syfte:** Tvinga källskydd i produktion - kan inte stängas av.

**Konfiguration:**
- Environment Variable: `SOURCE_SAFETY_MODE=true|false`
- Default: `true`
- Hard Mode: I produktion (`DEBUG=false`) är `SOURCE_SAFETY_MODE` ALLTID tvingat till `true`

**Beteende:**
- Development (`DEBUG=true`): `SOURCE_SAFETY_MODE` kan stängas av för testning
- Production (`DEBUG=false`): `SOURCE_SAFETY_MODE` är ALLTID `true` (tvingat)
- Om någon försöker sätta `false` → Boot fails med `ValueError`

### File Encryption

**Fil:** `backend/app/modules/projects/file_storage.py`

**Syfte:** Kryptera filer innan lagring på disk.

**Kryptering:**
- Algoritm: Fernet (symmetric encryption)
- Key: `PROJECT_FILES_KEY` (base64-encoded, från environment)
- Storage Format: Filer sparas som `{sha256}.bin` (ingen originalfilnamn på disk)

**Key Management:**
- Key måste vara säkert lagrad (secrets manager)
- Rotera regelbundet
- Logga aldrig key

### Integrity Verification

**Fil:** `backend/app/modules/projects/integrity.py`

**Syfte:** Verifiera integritet för alla artefakter i ett projekt.

**Hash Verification:**
- Notes: `note_integrity_hash` (SHA256 av body_text)
- Transcripts: `raw_integrity_hash` (SHA256 av raw content)
- Files: `sha256` (SHA256 av file content)

**Verification Endpoint:**
- `GET /api/v1/projects/{id}/verify`
- Returnerar: `integrity_ok`, `checked`, `issues`

### Autonomy Guard

**Fil:** `backend/app/modules/autonomy_guard/checks.py`

**Syfte:** Regelbaserade checks för att flagga potentiella problem (NO AI).

**Checks:**
1. Unusually Short Transcript (< 100 tecken)
2. Low Average Confidence (< 70%)
3. Rapid Deletion Activity (> 3 raderingar/timme)
4. Sensitive Project with Retained Files
5. Inactive Project with Content (> 90 dagar)

**Viktiga Principer:**
- NO AI: Alla checks är regelbaserade (deterministiska)
- Non-Blocking: Checks flaggar endast problem, blockar ALDRIG handlingar
- Audit Trail: Alla flags loggas i audit (utan content)

### Retention & Cleanup

**Fil:** `scripts/cleanup_retention.py`

**Syfte:** Rensa gamla filer och projekt enligt retention policy.

**Policy:**
- Default projects: `RETENTION_DAYS_DEFAULT` (30 dagar)
- Sensitive projects: `RETENTION_DAYS_SENSITIVE` (7 dagar)
- Temp files: `TEMP_FILE_TTL_HOURS` (24 timmar)

**Cleanup Process:**
1. Rensar temp files äldre än TTL
2. Rensar destroyed projects äldre än retention
3. Sensitive projects: kortare retention
4. Skapar audit event `system_cleanup_run` (utan content)

### Egress Control

**Fil:** `scripts/check_egress.py`

**Syfte:** Verifiera att backend inte kan nå externa endpoints (produktionskrav).

**Beteende:**
- Production (`DEBUG=false`): Förväntat `can_reach_external = False`
- Development (`DEBUG=true`): Status: `INFO` (informational only)

**Verification:**
- `scripts/check_egress.py` (manual check)
- `scripts/verify_no_internet.sh` (runtime verification)
- `make verify-brutal` (full verification)

---

## Operational Security

### Production Startup Procedure

**Pre-flight Checks:**
1. Verifiera secrets finns i `/run/secrets/`
2. Verifiera certifikat finns (CA, server, CRL)
3. Verifiera `PROFILE=prod_brutal` är satt
4. Verifiera att inga cloud API keys finns i env

**Start Services:**
1. Starta backend (via docker-compose.prod_brutal.yml)
2. Starta proxy (med mTLS config)
3. Verifiera health endpoints

**Post-startup Verification:**
1. Kör `make verify-brutal` (static + runtime validation)
2. Verifiera mTLS fungerar (TLS handshake fails utan cert, 200 med cert)
3. Verifiera zero egress (backend kan inte nå internet)
4. Verifiera Privacy Gate fungerar

### Debugging Without Data Leakage

**Principer:**
- Inga PII i logs (redan implementerat via Privacy Guard)
- Ingen payload/header/content logging i produktion
- Endast metadata: request_id, error_type, error_code, latency

**Tillåtna felsökningsmetoder:**
- Logga request_id och spåra via request_id
- Kör health/ready endpoints för status
- Använd `docker exec` för att inspektera container (kräver host access)
- Använd audit logs (användare, actions, timestamps - ingen content)

**Förbjudna felsökningsmetoder:**
- Aktivera "debug mode" via API/env
- Logga payloads/headers/content
- Dumpa databas eller filer till log
- Exponera debug endpoints publikt

### Log Policy

**Vad som får finnas i logs:**
- Request ID
- Error type (exception class name)
- Error code (internal error code)
- Timestamp
- Latency
- User role (från X-User-Role header)
- Action type (endpoint name, method)

**Vad som ALDRIG får finnas i logs:**
- PII (personnummer, email, telefon, namn)
- Payloads/request bodies
- Headers (förutom X-User-Role för audit)
- File paths
- Database queries med data
- Stack traces i produktion
- API keys eller secrets

**Log Storage:**
- Logs skrivs till stdout (Docker logging driver)
- Logs kan aggregeras av extern log system (t.ex. ELK, Loki)
- Logs har retention policy (t.ex. 30 dagar)
- Logs är krypterade i transit och at rest

### Docker Hardening

**Security Features:**
- Non-root user: `appuser` (uid 1000)
- Read-only filesystem: Utom `/app/data`
- Capabilities dropped: `cap_drop: ALL`
- No new privileges: `no-new-privileges:true`
- Tmpfs: `/tmp` och `/var/tmp` som tmpfs

**Network Isolation:**
- No egress: Backend får inte ha internet-egress i produktion
- Internal networks: Endast kommunikation inom Docker network
- Database: Inte exponerad externt

---

## Journalism Safety & Källskydd

### Minimera Metadata

**Princip:** Inget som kan identifiera en källa får hamna i logs eller audit trails.

**Förbjudna fält i logs/audit:**
- IP-adresser (`ip`, `client_ip`, `remote_addr`, `x-forwarded-for`)
- User-Agent (`user_agent`, `user-agent`)
- Referer/Origin (`referer`, `referrer`, `origin`)
- URLs (`url`, `uri`)
- Filnamn (`filename`, `filepath`, `original_filename`)
- Query strings (`querystring`, `query_string`)
- Cookies (`cookies`, `cookie`)
- Headers (`headers`)
- Host information (`host`, `hostname`)

**Beteende:**
- DEV mode: Systemet kastar `AssertionError` om förbjudna fält försöker loggas
- PROD mode: Systemet droppar fältet tyst och loggar ett säkert warning-event (utan innehåll)

### Source Safety Mode (Hard Mode)

**I produktion (`DEBUG=false`):**
- `SOURCE_SAFETY_MODE` är ALLTID tvingat till `true`
- Om någon försöker sätta `false` → Boot fails med `ValueError`
- Kan inte stängas av i produktion

**Rationale:**
- Källskydd är obligatoriskt för journalistisk användning
- Fail-fast vid försök att kompromissa säkerhet

### Transparens

**Princip:** Audit trails visar **vad som hände**, inte **vad som sades**.

**Vad audit visar:**
- Åtgärder (created, updated, exported, deleted)
- Timestamps
- Antal artefakter (counts)
- Format (srt, vtt, quotes)
- Status (ready, archived, destroyed)
- Receipt IDs för destruktion

**Vad audit ALDRIG visar:**
- Transcript-text
- Note-body
- File-content
- Original filnamn (i audit, endast i DB metadata)
- IP-adresser eller annan identifierande metadata

### Retention Policy

**Princip:** Inget material sparas längre än nödvändigt.

**Beteende:**
- Hard delete: När material raderas, raderas det permanent (med receipt)
- Inga automatiska backups av känsligt material
- Användare måste explicit exportera/arkivera om de vill behålla material

**För känsliga projekt:**
- Filer kan sparas som temp-only (dokumenteras per projekt)
- Överväg automatisk rensning efter X dagar (konfigurerbart)

### Human-in-the-Loop

**Princip:** Alla viktiga beslut kräver mänsklig bekräftelse.

**Regler:**
- Inga autonoma content-förändringar: Systemet ändrar aldrig innehåll automatiskt
- Inga "auto-share": Material delas aldrig automatiskt
- All export/destroy kräver explicit confirm: Användare måste bekräfta med `confirm: true` och ange `reason`

### Secure Delete Policy

**Vad vi garanterar:**
- Filer raderas från filsystemet
- Krypterade blobs tas bort (encrypted content)
- Best-effort overwrite (kan inte garanteras på SSD)
- Atomic two-phase destroy (pending → destroyed)
- Receipt för alla destruktiva handlingar

**Säkerhetsmodell:**
- Vi litar på **encryption-at-rest** + **deletion of encrypted blobs**
- Om filen är krypterad och blobben är raderad: innehållet är säkert även om fysiska bitar finns kvar
- För riktig garanti: Använd disk encryption (LUKS, BitLocker) + kontrollerad storage

**Vad vi INTE garanterar:**
- Fysisk overwrite på SSD (wear leveling, TRIM)
- Data recovery omöjlighet kräver disk encryption + kontrollerad storage
- Fysiska bitar kan finnas kvar på SSD även efter radering

---

## User Safety

### Original Lock

**Princip:** Original transcript får aldrig redigeras direkt.

**Beteende:**
- Original transcript är låst för redigering
- Endast ersättning via explicit endpoint
- Skyddar källmaterial från oavsiktlig förstörelse

### Dry-Run som Default

**Princip:** Farliga operationer körs i dry-run-läge som standard.

**Operationer med dry-run:**
- `destroy` (radera projekt)
- `export-and-destroy` (exportera och radera)

**Beteende:**
- Default: `dry_run=true`
- Kräver `{ confirm: true, reason: "..." }` för faktisk destruktion
- Returnerar vad som skulle hända utan att faktiskt göra det

### Receipt System

**Princip:** Alla destruktiva handlingar returnerar receipt.

**Receipt innehåller:**
- `receipt_id` (UUID för spårbarhet)
- `destroyed_at` (timestamp)
- `counts` (antal raderade artefakter)
- `reason` (användarens angivna anledning)

**Användning:**
- Spårbarhet för juridiska/etiska granskningar
- Verifiering att radering faktiskt skedde
- Audit trail för destruktiva operationer

### Human-in-the-Loop

**Princip:** Inga autonoma beslut - alltid mänsklig kontroll.

**Regler:**
- Inga autonoma content-förändringar: Systemet ändrar aldrig innehåll automatiskt
- Inga "auto-share": Material delas aldrig automatiskt
- All export/destroy kräver explicit confirm: Användare måste bekräfta med `confirm: true` och ange `reason`

**Autonomy Guard:**
- Regelbaserade checks (NO AI)
- Flaggar potentiella problem
- Rekommenderar åtgärder
- Blockar ALDRIG handlingar
- Användaren har alltid sista ordet

---

## Privacy Gate

### Security Guarantee

**Garanti:** Extern egress får endast `MaskedPayload` - aldrig raw text med direktidentifierande PII.

**Enforcement:**
- Privacy Gate (`privacy_gate.ensure_masked_or_raise()`) är enda sättet att förbereda text för extern egress
- Type-safe enforcement via `MaskedPayload` (kan endast skapas av Privacy Shield)
- Multi-pass masking säkerställer edge cases fångas
- Fail-closed leak check: ANY detected PII = BLOCK (422)

### API Endpoints

**POST /api/v1/privacy/mask**
- Maskera text med PII för extern egress
- Response (200 OK): `maskedText`, `entities`, `privacyLogs`, `provider`, `requestId`, `control`
- Response (422 PII Detected): `error` med `code: "pii_detected"`

**POST /api/v1/events/{event_id}/draft**
- Skapa draft för event med Privacy Gate enforcement
- Response (201 Created): `draft_id`, `event_id`, `content`, `created_at`
- Response (422 PII Detected): `error` med `code: "pii_detected"`

### Implementation

**Privacy Gate (`app.core.privacy_gate`):**
```python
from app.core.privacy_gate import ensure_masked_or_raise

# Prepare text for external LLM
masked_payload = await ensure_masked_or_raise(
    text=raw_text,
    mode="strict",
    request_id=request_id
)

# masked_payload.text is guaranteed to have no direct PII
```

**Draft Module:**
- OBLIGATORISKT använder Privacy Gate
- STEP 1: Privacy Gate (OBLIGATORY - no bypass possible)
- STEP 2: Create draft using masked text only

### Testing

**Test Privacy Shield Leak Prevention:**
- `make test-privacy`
- Testar edge case med 100 repetitioner av PII
- Förväntat resultat: PASS (ingen raw PII i output)

**Verify Privacy Chain:**
- `make verify-privacy-chain`
- Kör komplett verifiering:
  1. Privacy Shield leak prevention test
  2. Privacy gate usage check
  3. Draft privacy chain test

### CI/CD Enforcement

**Privacy Gate Usage Check:**
- `make check-privacy-gate` (kör `scripts/check_privacy_gate_usage.py`)
- Verifierar att:
  - Externa LLM-anrop använder `privacy_gate` eller `MaskedPayload`
  - `httpx`/`requests`/`openai` inte importeras utanför `app/modules/*/providers/`
  - Inga bypass-vägar finns

---

## Certificate Lifecycle

### Create Certificate

**Script:** `scripts/cert_create.sh`

**Användning:**
```bash
./scripts/cert_create.sh <user_id> <role> [days_valid]
```

**Process:**
1. Genererar privat nyckel (4096-bit RSA)
2. Skapar CSR (Certificate Signing Request) med CN=user_id, OU=role
3. Signerar certifikat med CA
4. Sparar certifikat och nyckel i `certs/` directory

**Distribution:**
- Certifikat och nyckel måste distribueras säkert till användare
- Metoder: USB-sticka, krypterad e-post, direktöverföring
- Användare installerar certifikat på sin dator

### Rotate Certificate

**Script:** `scripts/cert_rotate.sh`

**Användning:**
```bash
./scripts/cert_rotate.sh <user_id> [days_valid]
```

**Process:**
1. Extraherar roll från gammalt certifikat
2. Skapar nytt certifikat med samma user_id och roll
3. Gammalt certifikat förblir giltigt tills det revokeras
4. Distribuerar nytt certifikat till användare
5. Efter bekräftelse: revokera gammalt certifikat

**Timing:**
- Rotation sker före utgång (t.ex. vid 80% av giltighetstid)
- Standard giltighetstid: 90 dagar
- Rotation bör ske 10-20 dagar före utgång

### Revoke Certificate

**Script:** `scripts/cert_revoke.sh`

**Användning:**
```bash
./scripts/cert_revoke.sh <user_id> [--old]
```

**Process:**
1. Lägger till certifikat i CRL (Certificate Revocation List)
2. Uppdaterar CRL-fil
3. Restart proxy för att ladda ny CRL
4. Revokerat certifikat avvisas vid mTLS-verifiering (cert rejected during handshake) < 5 minuter efter proxy restart

**Användningsfall:**
- Certifikat kompromitterat (stöld, förlust)
- Användare lämnar organisationen
- Rotation (efter att nytt certifikat bekräftats)

### Emergency Disable

**Script:** `scripts/cert_emergency_disable.sh`

**Användning:**
```bash
./scripts/cert_emergency_disable.sh <user_id> <reason>
```

**Process:**
1. Omedelbar revokering av certifikat
2. Loggar emergency action separat (`certs/emergency-access.log`)
3. Uppdaterar CRL
4. Kräver manuell bekräftelse (säkerhetsåtgärd)

**Användningsfall:**
- Misstänkt säkerhetsincident
- Förlorad/stulen enhet
- Omedelbar blockering krävs

### CRL (Certificate Revocation List)

**Fil:** `certs/crl.pem`

**Hantering:**
- CRL support är planerad men inte aktivt konfigurerad i nuvarande Caddyfile
- Revokering sker via `scripts/cert_revoke.sh` (uppdaterar CRL-fil)
- Proxy måste restartas efter CRL-uppdatering för att ladda ny CRL
- CRL validering kommer att verifieras vid varje mTLS request när implementerat

**Uppdatering:**
```bash
# Efter revokering, restart proxy:
docker-compose -f docker-compose.prod_brutal.yml restart proxy
```

**Verifiering:**
- Revokerat certifikat avvisas vid mTLS-verifiering (cert rejected during handshake) < 5 minuter efter proxy restart
- Testa med: `curl -k --cert certs/user-123.crt --key certs/user-123.key https://localhost/api/v1/example`

---

## Incident Response

### Incident Kategorier

**Kategori 1: Security Incident**
- Certifikatstöld
- Obehörig åtkomst
- Misstänkt kompromittering

**Process:**
1. Identifiera Incident
2. Omedelbar Åtgärd (< 5 minuter): Revokera kompromitterat certifikat
3. Granska Loggar
4. Kommunikera (Intern: Tech Lead, Security Lead, Operations)
5. Dokumentera

**Tidslinje:**
- Omedelbar revokering: < 5 minuter
- Granskning: < 1 timme
- Dokumentation: < 24 timmar

**Kategori 2: System Failure**
- Backend crash
- Proxy nere
- Database connection lost

**Process:**
1. Identifiera Problem
2. Isolera Problem
3. Återställ Systemet
4. Verifiera
5. Dokumentera

**Tidslinje:**
- Identifiera: < 5 minuter
- Återställ: < 15 minuter
- Verifiera: < 5 minuter
- Dokumentation: < 24 timmar

**Kategori 3: Data Breach (Potential PII Leak)**
- Misstänkt PII leakage
- Privacy Gate failure
- External API leak

**Process:**
1. Identifiera Misstänkt Leakage
2. Omedelbar Isolation
3. Identifiera Scope
4. Verifiera Leakage
5. Om Bekräftat Leakage: Notify relevant authorities (GDPR)
6. Dokumentera

**Tidslinje:**
- Isolation: < 5 minuter
- Scope identification: < 1 timme
- Verification: < 4 timmar
- Notification (om bekräftat): < 72 timmar (GDPR-krav)

### Break-Glass Procedure

**När:** Kritiska incidenter där normal access-control måste kringgås

**Process:**
1. Fysisk/Host Access Krävs
2. Använd Emergency Certifikat
3. Logga All Access
4. Time-Limited
5. Post-Incident Review

**Säkerhetsgarantier:**
- Emergency certifikat kräver fysisk/host access
- All access loggas separat
- Emergency certifikat har automatisk utgång
- Process dokumenteras och granskas

### Communication Plan

**Intern Kommunikation:**
- Tech Lead: Alla incidenter, system failures, security incidents
- Security Lead: Security incidents, data breaches, break-glass usage
- Operations: System failures, operational issues, deployment problems

**Extern Kommunikation:**
- Endast om: Data breach bekräftats (GDPR-krav), personuppgifter faktiskt har läckt, relevant authority måste notifieras

**Process:**
1. Verifiera leakage faktiskt skedde
2. Identifiera scope (vilka data, vilka användare)
3. Notify relevant authority (t.ex. Datainspektionen)
4. Notify affected users
5. Document notification

---

## Verification & Testing

### Automated Verification

**Static Validation:**
- `scripts/validate_del_a.sh` - Docker compose and Caddyfile validation
- `scripts/check_privacy_gate_usage.py` - Privacy Gate enforcement check

**Runtime Validation:**
- `make verify-brutal` - Full security profile verification
- `make verify-privacy-chain` - Privacy chain verification
- `make verify-phase-b-runtime` - Phase B runtime verification med evidence pack
- `scripts/verify_mtls.sh` - mTLS verification (TLS handshake fail utan cert, 200 med cert)
- `scripts/verify_no_internet.sh` - Zero egress verification

**CI/CD:**
- All verification scripts run in CI (se `.github/workflows/`)
- Documentation validation (`make check-docs` kör `scripts/check_docs.sh`)

### Manual Testing

**Security Tests:**
- Privacy Shield leak prevention tests (se `tests/results/` för testrapporter)
- Comprehensive security test (A-Z security audit, se `tests/results/AZ_SECURITY_RAPPORT.md` om filen finns)
- Cold start rehearsal (operational realism, se `docs/COLD_START_REHEARSAL.md` om filen finns)

**Test Results:**
- `tests/results/AZ_SECURITY_RAPPORT.md` - Security audit report (om filen finns)
- Privacy Shield leak prevention test results (se `tests/results/` för faktiska rapporter)

### Regular Checks

**Daglig:**
- Egress check (`scripts/check_egress.py`)
- Log hygiene check (`scripts/check_logs.py` - om scriptet finns)
- Privacy Guard enforcement (automatisk via `source_safety_mode` och Privacy Guard)

**Veckovis:**
- Integrity verification
- Security audit review

**Månadsvis:**
- Full threat model review
- Security policy review

---

## Risk Assessment

### Medvetet Accepterade Risker

**Risk 1: Certifikatstöld**
- **Sannolikhet:** Låg (certifikat är fysiskt skyddade)
- **Impact:** Hög (stulen cert ger full access)
- **Mitigation:** Certifikat-rotation, revokering, emergency disable
- **Acceptans:** Vi accepterar denna risk i utbyte mot zero egress och mTLS-säkerhet

**Risk 2: Manuell certifikat-hantering**
- **Sannolikhet:** Medel (mänskligt fel vid rotation/revokering)
- **Impact:** Medel (certifikat kan bli ogiltiga om fel hanteras)
- **Mitigation:** Dokumenterade procedurer, training
- **Acceptans:** Vi accepterar denna risk i utbyte mot zero egress

**Risk 3: Operativt misstag (felhantering läcker data)**
- **Sannolikhet:** Medel (mänskligt fel)
- **Impact:** Hög (PII leakage)
- **Mitigation:** Log policy, felsökningsprocedurer, training
- **Acceptans:** Vi accepterar denna risk med strikt log policy och procedurer

**Risk 4: Frontend-exponering öppnar nya attackytor**
- **Sannolikhet:** Låg (frontend är statiska filer)
- **Impact:** Medel (XSS, CSRF)
- **Mitigation:** Security headers (CSP, X-Frame-Options)
- **Acceptans:** Vi accepterar denna risk med security headers och frontend best practices

### Residual Risks

**Accepterade Risker:**
- Authentication: CORE har ingen authentication (kommer i framtida modul)
- Backup/Recovery: Inga automatiska backups (enligt policy)

**Utanför Scope:**
- Production deployment automation
- Load balancing
- High availability
- Disaster recovery (utöver retention policy)

---

## Compliance & Regulatory

### GDPR Compliance

**Data Minimization:**
- Privacy Gate maskerar PII innan externa AI-anrop
- Inga raw PII skickas till externa AI:er
- Retention policy (automatisk purge efter X dagar)

**Right to Deletion:**
- `POST /api/v1/record/{transcript_id}/destroy` (destroy record med dry_run default)
- Purge module (automatisk rensning efter retention)

**Data Protection:**
- File encryption (Fernet)
- Secret management (Docker secrets)
- Privacy-safe logging (ingen PII i logs)

**Verification:**
- Privacy chain verification
- Log policy compliance
- Retention policy verification

### Journalistic Source Protection

**Source Safety:**
- Privacy-safe logging (ingen IP, user-agent, referrer)
- Source protection mode (forced in production)
- No PII in audit logs

**Verification:**
- Log policy compliance
- Privacy guard verification

### Juridiska & Etiska Krav

**Källskydd (Sverige):**
- Tryckfrihetsförordningen: Skyddar källor och källmaterial
- Offentlighetsprincipen: Balans mellan transparens och källskydd
- GDPR: Personuppgifter ska minimeras och skyddas

**Copy/Paste följer:**
- Minimering av metadata som kan identifiera källor
- Kryptering av känsligt material
- Möjlighet att permanent radera material (med receipt)

**Etiska Principer:**
- Transparens: Process-spårbarhet utan innehåll
- Mänsklig kontroll: Inga autonoma beslut
- Minimering: Inget material sparas längre än nödvändigt
- Källskydd: Inget som kan identifiera källor i logs/audit

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
- Read-only filesystem
- Non-root user
- Regular cleanup runs

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

## Support & Resources

### Dokumentation

**Teknisk dokumentation:**
- `docs/core.md` - Core Backend Foundation
- `docs/architecture.md` - System Architecture
- `docs/getting-started.md` - Startup Guide

**Säkerhetsdokumentation:**
- `docs/security-complete.md` (denna fil) - Komplett säkerhetsdokumentation

**Operational dokumentation:**
- Certificate lifecycle: Se [Certificate Lifecycle](#certificate-lifecycle) sektion i denna fil
- Incident response: Se [Incident Response](#incident-response) sektion i denna fil

### Kontakt

För frågor om säkerhet:
- Kontakta IT-säkerhetsteamet
- Se `docs/core.md` för tekniska detaljer
- Se `docs/getting-started.md` för operativa rutiner

---

**Status:** ✅ Production Ready - Security Baseline Complete

**Version:** 1.0.0  
**Senast uppdaterad:** 2025-12-25

---

## AI-Assistent Regler (Maskinläsbar Säkerhet)

**Detta avsnitt är obligatoriskt för alla AI-assistenter som arbetar i detta repo.**

### Obligatoriska Dokument
Innan du gör ändringar, läs:
1. `docs/agent.md` - Konstitution och arbetsregler
2. `docs/security-complete.md` (detta dokument) - Exakt säkerhetssemantik
3. `docs/core.md` - Module Contract och backend-regler
4. `docs/UI_STYLE_TOKENS.md` - UI-stil lås

### Security Invariants (Testbara Checks)
Alla invariants är kodade i `scripts/check_security_invariants.py` och körs via:
- `make check-security-invariants` (statisk gate)
- `make verify-brutal` (runtime gate)

**Om en invariant bryts → verifieringen failar → ändringen stoppas.**

### Förändringsregel
Varje ändring som berör säkerhet måste:
1. Köra `make check-security-invariants`
2. Köra `make verify-brutal` (eller relevant verify-*)
3. Uppdatera `docs/security-complete.md` om semantik ändras
4. Uppdatera `docs/UI_API_INTEGRATION_REPORT.md` om UI↔API ändras

### Superprompt
För att säkerställa att olika AI-modeller följer samma regler, använd `docs/AGENT_SUPERPROMPT.md` som startregel.

**Detta gör säkerheten maskinläsbar, testbar och fail-closed.**

