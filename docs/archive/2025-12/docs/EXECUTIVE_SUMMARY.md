<!--
ARCHIVED DOCUMENT
This file is no longer authoritative.
Canonical source of truth: docs/canonical/
-->

# Executive Summary - Copy/Paste

**Version:** 1.0.0  
**Senast uppdaterad:** 2025-12-25

---

## Vad är Copy/Paste?

Copy/Paste är ett **journalistiskt AI-assistanssystem** med fokus på källskydd, dataskydd och integritet. Systemet är designat för att hantera känsligt journalistiskt material (transkriptioner, källkontakter, artiklar) med maximal säkerhet.

### Huvudsyfte

- **Transkribering:** Ladda upp ljudfiler, transkribera automatiskt (faster-whisper), hantera transkriptioner
- **Projekthantering:** Organisera material i projekt med start/due dates, känslighetsnivåer
- **Källskydd:** Privacy Gate blockerar PII-leakage, zero egress förhindrar externa anrop
- **GDPR-compliance:** Krypterad lagring, retention policies, secure deletion

---

## Hur Säkerheten Hålls

### Hårda Invariants (Testbara, Maskinläsbara)

1. **Zero Egress (prod_brutal)**
   - Backend kan inte nå internet via Docker network
   - `ensure_egress_allowed()` blockerar alla externa providers
   - Boot fail om cloud API keys är satta

2. **mTLS Enforcement**
   - Alla HTTPS-requests på 443 kräver klientcertifikat
   - Utan cert: TLS handshake failar
   - Health/ready: Endast HTTP (80) för driftmonitoring

3. **Privacy Gate**
   - Extern egress endast med `MaskedPayload`
   - Ingen raw text med PII får nå externa providers
   - Leak → 422 (fail-closed)

4. **No-Content Logging**
   - Inga payloads/headers/PII/content i logs
   - Endast metadata (counts, ids, format)

5. **Fail-Closed Design**
   - Osäker config i prod_brutal → boot fail
   - Hellre nere än osäkert

**Verifiering:** `make check-security-invariants` (statisk gate) och `make verify-brutal` (runtime gate)

**Detaljer:** Se [SECURITY_MODEL.md](canonical/SECURITY_MODEL.md)

---

## Hur Man Bygger Nytt Utan Att Bryta Något

### Module Contract

**Alla moduler följer Module Contract v1:**
- Endast importera från `app.core.logging` och `app.core.config`
- Privacy-safe logging (inga payloads/headers/PII)
- DB-optional design (moduler fungerar även om DB saknas)
- Dokumentation i `README.md`

**Detaljer:** Se [MODULE_MODEL.md](canonical/MODULE_MODEL.md)

### Säkerhetschecklist

**Innan du gör ändringar:**
1. Läs canonical docs i `docs/canonical/`
2. Kör `make check-security-invariants` (statisk gate)
3. Kör `make verify-brutal` (runtime gate)
4. Uppdatera canonical docs om semantik ändras

**Detaljer:** Se [AI_GOVERNANCE.md](canonical/AI_GOVERNANCE.md)

---

## Hur AI Hålls i Schack

### Single Entry Point

**Alla AI-sessioner börjar här:**
1. Läs `docs/agent.md` (entry point)
2. Läs canonical docs i `docs/canonical/`
3. Följ arbetsregler i `docs/canonical/AI_GOVERNANCE.md`

**Tid:** < 10 minuter för att förstå systemet

### Maskinläsbar Säkerhet

**Alla invariants är kodade i `scripts/check_security_invariants.py`:**
- `make check-security-invariants` (statisk gate)
- `make verify-brutal` (runtime gate)

**Om en invariant bryts → verifieringen failar → ändringen stoppas.**

**Detaljer:** Se [AI_GOVERNANCE.md](canonical/AI_GOVERNANCE.md)

---

## Dokumentationsstruktur

### Canonical Docs (Single Source of Truth)

**6 canonical docs i `docs/canonical/`:**
- `SYSTEM_OVERVIEW.md` - Vad systemet är
- `SECURITY_MODEL.md` - Säkerhetsgarantier
- `MODULE_MODEL.md` - Hur moduler byggs
- `DATA_LIFECYCLE.md` - Datahantering
- `AI_GOVERNANCE.md` - AI-regler
- `OPERATIONAL_PLAYBOOK.md` - Drift

**Alla andra docs länkar uppåt till canonical docs.**

**Verifiering:** `make check-docs-integrity` (automatisk verifiering)

**Detaljer:** Se [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) och [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md)

---

## Snabbstart

### Starta Systemet

```bash
# 1. Starta backend + database
make up

# 2. Starta frontend (i separat terminal)
make frontend-dev

# 3. Öppna webbläsaren
open http://localhost:5174
```

**Detaljer:** Se [OPERATIONAL_PLAYBOOK.md](canonical/OPERATIONAL_PLAYBOOK.md)

---

## Referenser

- **Canonical Docs:** `docs/canonical/`
- **Documentation Map:** `docs/DOCUMENTATION_MAP.md`
- **Documentation Rules:** `docs/DOCUMENTATION_RULES.md`
- **Agent Entry Point:** `docs/agent.md`

---

**Detta är det enda dokument en människa måste läsa först. Allt annat länkar härifrån.**

