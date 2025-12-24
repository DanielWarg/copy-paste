# Threat Model - Hotanalys

Detta dokument beskriver hotmodellen för Copy/Paste och hur systemet skyddar mot dessa hot.

## Översikt

Copy/Paste är designat för journalistisk användning med känsligt material. Hotmodellen fokuserar på källskydd, dataskydd och integritet.

## Hotkategorier

### 1. Källidentifiering

**Hot:** Attacker eller myndigheter försöker identifiera källor genom metadata.

**Skydd:**
- Inga IP-adresser i logs/audit
- Inga filnamn i logs/audit
- Inga URLs i logs/audit
- Inga user-agents i logs/audit
- SOURCE_SAFETY_MODE forced i produktion

**Verifiering:**
- `scripts/test_source_safety.py`
- `scripts/check_logs.py`
- `make verify`

### 2. Content Leakage

**Hot:** Känsligt innehåll läcker i logs, audit trails eller felmeddelanden.

**Skydd:**
- Privacy Guard blockerar content-fält
- Audit trails innehåller endast metadata (counts, ids, format)
- Error messages är generiska i produktion
- Inga stack traces i produktion

**Verifiering:**
- `scripts/test_source_safety.py`
- `scripts/check_logs.py`
- Manual log review

### 3. Data Exfiltration

**Hot:** Attacker försöker stjäla känsligt material.

**Skydd:**
- Ingen internet-egress för backend i produktion
- File encryption (Fernet)
- Filer sparas som `{sha256}.bin` (ingen originalfilnamn)
- Read-only filesystem (utom `/app/data`)

**Verifiering:**
- `scripts/check_egress.py`
- Network isolation checks
- File encryption verification

### 4. Unauthorized Access

**Hot:** Obefintlig användare får tillgång till systemet.

**Skydd:**
- (Framtida: Authentication/authorization module)
- Docker hardening (non-root, capabilities dropped)
- Network isolation
- Security headers

**Status:**
- Authentication är utanför scope för CORE
- Kommer i framtida modul

### 5. Data Corruption

**Hot:** Data korrupteras eller förändras oavsiktligt.

**Skydd:**
- Integrity hashes (SHA256)
- Verification endpoint (`/api/v1/projects/{id}/verify`)
- Original lock (transcripts kan inte redigeras direkt)
- Audit trails för alla ändringar

**Verifiering:**
- Integrity verification tests
- Hash verification

### 6. Accidental Deletion

**Hot:** Användare raderar material oavsiktligt.

**Skydd:**
- Dry-run som default
- Explicit confirm krävs
- Receipt system för spårbarhet
- Human-in-the-loop (inga autonoma beslut)

**Verifiering:**
- User safety tests
- Dry-run verification

### 7. Metadata Leakage

**Hot:** Metadata som kan identifiera källor läcker.

**Skydd:**
- Source Safety Mode (forced i prod)
- Privacy Guard blockerar källidentifierare
- Log minimization
- Inga query strings i logs

**Verifiering:**
- Source safety tests
- Log hygiene checks

## Mitigation Strategies

### Defense in Depth

**Lager 1: Privacy Guard**
- Blockar content och källidentifierare i logs/audit
- Fail-fast i DEV, fail-safe i PROD

**Lager 2: Source Safety Mode**
- Hard mode i produktion (kan inte stängas av)
- Ytterligare fält förbjuds

**Lager 3: File Encryption**
- Alla filer krypteras innan lagring
- Ingen originalfilnamn på disk

**Lager 4: Network Isolation**
- Ingen internet-egress för backend
- Interna nätverk endast

**Lager 5: Docker Hardening**
- Non-root user
- Read-only filesystem
- Capabilities dropped
- No new privileges

### Fail-Safe Defaults

**Princip:** Systemet failar säkert vid osäkerhet.

**Exempel:**
- Om SOURCE_SAFETY_MODE försöker stängas av i prod → Boot fails
- Om content försöker loggas → Droppas tyst i PROD, AssertionError i DEV
- Om egress finns → Warning, dokumenterat krav

## Attack Scenarios

### Scenario 1: Log Injection

**Attack:** Attacker försöker injicera källidentifierare i logs.

**Mitigation:**
- Privacy Guard sanitizerar all log-data
- Source Safety Mode blockerar källidentifierare
- AssertionError i DEV vid överträdelser

**Verifiering:**
- `scripts/test_source_safety.py`
- `scripts/check_logs.py`

### Scenario 2: File Theft

**Attack:** Attacker försöker stjäla filer från disk.

**Mitigation:**
- Filer krypterade (Fernet)
- Filer sparas som `{sha256}.bin` (ingen originalfilnamn)
- Read-only filesystem (utom `/app/data`)

**Verifiering:**
- File encryption tests
- Storage path verification

### Scenario 3: Metadata Correlation

**Attack:** Attacker korrelerar metadata för att identifiera källor.

**Mitigation:**
- Minimal metadata i logs/audit
- Inga timestamps som kan korreleras med externa events
- Inga IP-adresser eller user-agents

**Verifiering:**
- Source safety tests
- Log hygiene checks

## Residual Risks

### Accepterade Risker

**Authentication:**
- CORE har ingen authentication (kommer i framtida modul)
- Risk: Obefintlig användare kan komma åt systemet
- Mitigation: Network isolation, Docker hardening

**Backup/Recovery:**
- Inga automatiska backups (enligt policy)
- Risk: Data går förlorat vid hårdvarufel
- Mitigation: Explicit export/archive av användare

### Utanför Scope

- Production deployment automation
- Load balancing
- High availability
- Disaster recovery (utöver retention policy)

## Verification

### Regular Checks

**Daglig:**
- Egress check (`check_egress.py`)
- Log hygiene check (`check_logs.py`)

**Veckovis:**
- Integrity verification
- Security audit review

**Månadsvis:**
- Full threat model review
- Security policy review

## Support

För frågor om threat model:
- Se `docs/security.md` för tekniska säkerhetsdetaljer
- Se `docs/opsec.md` för operativa säkerhetsrutiner
- Kontakta IT-säkerhetsteamet

