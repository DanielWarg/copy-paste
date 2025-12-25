<!--
ARCHIVED DOCUMENT
This file is no longer authoritative.
Canonical source of truth: docs/canonical/
-->

# Security Phase B - Implementation Guide

**Datum:** 2025-12-24  
**Status:** Implementation in progress  
**Förutsättning:** Phase A (Brutal Security Profile v3.1 + Privacy Chain) är implementerad och verifierad

---

## Grundregel (Orubblig)

**Phase B får aldrig ändra, försvaga eller kringgå Phase A.**  
Allt byggs ovanpå, aldrig inuti.

---

## Steg 0 — Pre-flight (Obligatoriskt)

### Mål
Säkerställa att Phase A är orörd innan något ändras.

### Verifiering

```bash
# Kör full regression
make verify-brutal
make verify-privacy-chain
```

### Phase A Baseline

**Commit/Hash:** `[TO BE DOCUMENTED AFTER VERIFICATION]`  
**Status:** ✅ Phase A locked (referenspunkt)

**Verifierade garantier:**
- ✅ Zero egress (infrastructure + code-level)
- ✅ mTLS enforcement (proxy-level)
- ✅ Privacy Gate fail-closed
- ✅ Fail-closed design (boot fail om osäkert)

---

## Steg 1 — Access & Identity (Proxy-lager, ej backend)

### Mål
Certifikat → roll → header (utan auth-logik i backend)

### Implementation

**Caddy Certificate Metadata Parsing:**

Caddy kan extrahera certifikat-metadata via placeholders:
- `{tls.client.certificate_subject}` - Full subject (CN=user_id,OU=role,O=CopyPaste)
- `{tls.client.certificate_pem}` - Full certificate PEM

**Certifikat-struktur:**
```
CN=user_id (UUID eller hashed identifier)
O=CopyPaste
OU=role (journalist, redaktör, admin)
```

**Caddyfile-ändringar:**

Proxy injectar headers:
- `X-User-Id` - Från CN
- `X-User-Role` - Från OU
- `X-User-Org` - Från O (för verifiering)

**Backend:**
- Läser headers endast för audit/log
- Ingen access control-logik
- Headers är read-only (proxy ansvarar för validering)

### Verifiering

- Utan cert → 403
- Med giltigt cert → 200, headers satta
- Revokerat cert → 403 (CRL validering)

---

## Steg 2 — Certificate Lifecycle (Manuell, kontrollerad)

### Mål
Säker drift, inte automation-kaos

### Procedures

**1. Cert Create:**
- Script: `scripts/cert_create.sh <user_id> <role>`
- Genererar cert med CN=user_id, OU=role
- Signeras av CA
- Distribueras säkert (USB, encrypted email)

**2. Cert Rotation (90 dagar):**
- Script: `scripts/cert_rotate.sh <user_id>`
- Genererar nytt cert
- Distribuerar till användare
- Gammalt cert fungerar tills rotation
- Efter rotation: gammalt cert revokeras

**3. Cert Revocation:**
- Script: `scripts/cert_revoke.sh <user_id>`
- Lägger till cert i CRL
- Uppdaterar CRL-fil
- Restart proxy för att ladda CRL
- Revokerat cert ger 403 < 5 min

**4. Emergency Disable:**
- Script: `scripts/cert_emergency_disable.sh <user_id>`
- Omedelbar revokering
- Loggas separat (emergency-access.log)
- Kräver fysisk/host access

### Dokumentation

- `docs/certificate-lifecycle.md` - Komplett guide
- `scripts/cert_*.sh` - Alla cert-scripts

---

## Steg 3 — Operational Security (Människan i systemet)

### Mål
Drift utan dataläckage

### Implementation

**1. Startup Checklist:**
- `docs/operational-startup.md` - Production startup procedure
- Pre-flight checks
- Post-startup verification

**2. Debug-regler:**
- `docs/operational-debugging.md` - Vad är tillåtet/förbjudet
- Inga payloads i logs
- Inga debug-switchar i prod

**3. Incident Playbook:**
- `docs/incident-playbook.md` - Kategorier och procedurer
- Security incident
- System failure
- Data breach

### Verifiering

- Cold-start rehearsal körbar
- Incident kan hanteras utan dataexponering
- Log policy följs (0% PII i logs)

---

## Steg 4 — Frontend Exposure (Sist, kontrollerat)

### Mål
UI utan ny attackyta

### Implementation

**Frontend:**
- Statiska filer via proxy (`/ui/*`)
- mTLS krävs även för UI
- Security headers (CSP, X-Frame-Options)

**API:**
- Endast `/api/*` exponeras
- Health separat (`/health`, `/ready`)

**Caddyfile-ändringar:**
- Frontend static files route
- API route
- Health route (separat, minimal mTLS)

### Verifiering

- UI fungerar
- API fungerar
- Health endpoints isolerade
- Security headers sätts korrekt

---

## Steg 5 — Phase B Verification & Sign-off

### Mål
Bevisa att Phase B inte brutit Phase A

### Verification Tests

**1. Phase A Regression:**
```bash
make verify-brutal
make verify-privacy-chain
# Alla tester måste fortfarande passera
```

**2. Phase B Verification:**
```bash
make verify-phase-b
# Testar alla Phase B-kriterier
```

### Sign-off Checklist

- [ ] Tech Lead: Alla tekniska kriterier uppfyllda
- [ ] Security Lead: Säkerhetskriterier uppfyllda, ingen kompromiss av Phase A
- [ ] Operations: Operational procedures testade och fungerar
- [ ] Product: Funktionalitet matchar behov

---

## Status

**Steg 0:** ⏳ In progress  
**Steg 1:** ⏸️ Pending  
**Steg 2:** ⏸️ Pending  
**Steg 3:** ⏸️ Pending  
**Steg 4:** ⏸️ Pending  
**Steg 5:** ⏸️ Pending

---

**Nästa steg:** Kör Steg 0 verification och dokumentera Phase A baseline.

