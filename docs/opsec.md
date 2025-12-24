# Operational Security (OPSEC)

Detta dokument beskriver operativa säkerhetskrav för Copy/Paste i produktion.

## Översikt

Copy/Paste är designat för journalistisk användning med känsligt material. Operativa säkerhetskrav är kritiska för att skydda källor och material.

## Kritiska Krav

### 1. Ingen Internet Egress för Backend

**Krav:** Backend-containern får INTE ha internet-egress i produktion.

**Rationale:**
- Förhindrar oavsiktlig data-läcka
- Förhindrar exfiltration av känsligt material
- Minskar attack-yta

**Verifiering:**
```bash
# Kör egress check
python scripts/check_egress.py
```

**Förväntat resultat i produktion:**
- Status: `PASS`
- Message: "Backend cannot reach external endpoints (as required in production)"

**Implementering:**
- Docker: Använd `--network none` eller begränsa till intern nätverk
- Kubernetes: Använd NetworkPolicy för att blockera egress
- Cloud: Använd security groups/firewall rules

**Dokumentation:**
- Se `scripts/check_egress.py` för verifieringsscript
- Kör check vid deployment och regelbundet i produktion

### 2. Source Safety Mode (Hard Mode)

**Krav:** `SOURCE_SAFETY_MODE` är ALLTID `true` i produktion.

**Rationale:**
- Källskydd är obligatoriskt för journalistisk användning
- Kan inte stängas av i produktion

**Beteende:**
- Om `DEBUG=false` och `SOURCE_SAFETY_MODE=false` → Boot fails med `ValueError`
- Systemet tvingar automatiskt `SOURCE_SAFETY_MODE=true` i produktion

**Verifiering:**
```bash
# Testa att boot failar om SOURCE_SAFETY_MODE=false i prod
DEBUG=false SOURCE_SAFETY_MODE=false python -c "from app.core.config import settings"
# Förväntat: ValueError
```

### 3. Retention Policy

**Krav:** Material raderas enligt retention policy.

**Policy:**
- Default projects: `RETENTION_DAYS_DEFAULT` (default: 30 dagar)
- Sensitive projects: `RETENTION_DAYS_SENSITIVE` (default: 7 dagar)
- Temp files: `TEMP_FILE_TTL_HOURS` (default: 24 timmar)

**Implementering:**
- Cleanup script: `scripts/cleanup_retention.py`
- Kör regelbundet (cron/kubernetes job)
- Audit-loggar cleanup runs (utan content)

**Verifiering:**
```bash
# Kör cleanup
python scripts/cleanup_retention.py
```

### 4. Read-Only Filesystem

**Krav:** Container filesystem är read-only (utom `/app/data`).

**Rationale:**
- Förhindrar oavsiktlig filskrivning
- Minskar attack-yta
- Tvingar explicit data-hantering

**Implementering:**
- Docker: `read_only: true` + `tmpfs` för `/tmp`
- Writable volume endast för `/app/data`

**Verifiering:**
```bash
# Testa att skriva till read-only filesystem
docker exec <container> touch /app/test.txt
# Förväntat: Permission denied (utom i /app/data)
```

### 5. Non-Root User

**Krav:** Container kör som non-root user.

**Rationale:**
- Minskar risk vid container escape
- Följer security best practices

**Implementering:**
- Dockerfile: `USER appuser` (uid 1000)
- Verifiera i deployment

### 6. Capabilities Dropped

**Krav:** Alla capabilities droppas (`cap_drop: ALL`).

**Rationale:**
- Minskar privilegier
- Följer principle of least privilege

**Implementering:**
- Docker Compose: `cap_drop: [ALL]`
- Kubernetes: `securityContext.capabilities.drop: [ALL]`

### 7. No New Privileges

**Krav:** Container kan inte eskalera privilegier (`no-new-privileges:true`).

**Rationale:**
- Förhindrar privilege escalation
- Säkerhetsbest practice

**Implementering:**
- Docker Compose: `security_opt: [no-new-privileges:true]`
- Kubernetes: `securityContext.allowPrivilegeEscalation: false`

## Deployment Checklist

Före deployment i produktion:

- [ ] Backend har ingen internet-egress (verifiera med `check_egress.py`)
- [ ] `SOURCE_SAFETY_MODE=true` (tvingat i prod)
- [ ] `DEBUG=false`
- [ ] Read-only filesystem (utom `/app/data`)
- [ ] Non-root user
- [ ] Capabilities dropped
- [ ] No new privileges
- [ ] Retention cleanup är konfigurerad (cron/job)
- [ ] `PROJECT_FILES_KEY` är satt och säkert lagrat
- [ ] Database är inte exponerad externt
- [ ] Logs går till säker destination (ingen content leakage)

## Monitoring & Verification

### Regelbundna Checks

**Daglig:**
- Egress check (`check_egress.py`)
- Retention cleanup (`cleanup_retention.py`)

**Veckovis:**
- Integrity verification (`/api/v1/projects/{id}/verify`)
- Security audit review

**Månadsvis:**
- Full security audit
- Policy review

### Incident Response

Om säkerhetsincident upptäcks:

1. **Isolera:** Stoppa backend omedelbart
2. **Dokumentera:** Logga incident (utan content)
3. **Analysera:** Undersök vad som hände (audit logs)
4. **Åtgärda:** Fixa säkerhetshål
5. **Verifiera:** Kör alla checks igen
6. **Rapportera:** Informera relevanta parter

## Best Practices

### Development vs Production

**Development:**
- Egress tillåten (för utveckling)
- `DEBUG=true` möjligt
- `SOURCE_SAFETY_MODE` kan stängas av

**Production:**
- Ingen egress (hard requirement)
- `DEBUG=false` (hard requirement)
- `SOURCE_SAFETY_MODE=true` (hard requirement, tvingat)

### Network Isolation

**Rekommendation:**
- Backend i privat nätverk
- Endast frontend kan nå backend
- Database i privat nätverk
- Inga externa connections från backend

### Secrets Management

**Krav:**
- `PROJECT_FILES_KEY` från säker secrets manager
- Rotera regelbundet
- Logga aldrig secrets

## Support

För frågor om OPSEC:
- Se `docs/journalism-safety.md` för källskydd
- Se `docs/security.md` för tekniska säkerhetsdetaljer
- Kontakta IT-säkerhetsteamet

