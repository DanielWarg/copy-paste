# Security Model - Copy/Paste

**Version:** 1.0.0  
**Status:** Canonical Document (Single Source of Truth)  
**Senast uppdaterad:** 2025-12-25

---

## Säkerhetsgarantier (Hårda Invariants)

Dessa garantier är **testbara, maskinläsbara och fail-closed**. De får **ALDRIG** brytas.

### Invariant 1: Zero Egress (prod_brutal)

**Infrastructure Level:**
- `internal_net: internal: true` → Ingen gateway, ingen egress
- I prod_brutal runtime kan backend **INTE** nå internet via Docker network
- För att bryta detta krävs administrativ åtkomst och ändring av driftkonfiguration

**Code Level:**
- `ensure_egress_allowed()` blockerar egress i `prod_brutal` profile (raise `EgressBlockedError`)
- Alla externa providers måste kalla `ensure_egress_allowed()` innan network requests
- Startup check: Boot fail om cloud API keys (t.ex. `OPENAI_API_KEY`) är satta i env i prod_brutal

**Verification:**
- `scripts/verify_no_internet.sh` (runtime verification)
- `make verify-brutal` (full verification)
- `make check-security-invariants` (statisk gate)

**Maskinläsbar check:** `scripts/check_security_invariants.py` → `check_zero_egress_network()`

---

### Invariant 2: mTLS Enforcement

**Proxy Level:**
- `client_auth require_and_verify` i Caddyfile (port 443)
- Alla HTTPS-requests kräver giltigt klientcertifikat (TLS handshake fail utan cert)
- Health/readiness endpoints är tillgängliga via HTTP (port 80) utan mTLS för driftmonitoring

**Verification:**
- `scripts/verify_mtls.sh` (TLS handshake fail utan cert, 200 med cert)
- `make verify-brutal` (full verification)

**Maskinläsbar check:** `scripts/check_security_invariants.py` → `check_mtls_required()`

---

### Invariant 3: Privacy Gate

**Type-Safe Enforcement:**
- `MaskedPayload` är enda tillåtna input för externa LLM providers
- Privacy Gate är obligatorisk (`privacy_gate.ensure_masked_or_raise()`)
- Inget raw text kan nå externa AI:er utan att passera Privacy Gate

**Multi-Pass Masking:**
- Pass 1: Initial masking (regex: email, phone, PNR, etc.)
- Pass 2: Re-mask on result (catches overlaps, edge cases)
- Pass 3 (strict mode): Ytterligare pass för maximum safety

**Fail-Closed Leak Check:**
- ANY detected PII = BLOCK (422)
- No compromise, no fallback

**Verification:**
- `make verify-privacy-chain` (privacy chain verification)
- `make check-privacy-gate` (statisk gate)
- Privacy Shield leak prevention tests

**Maskinläsbar check:** `scripts/check_security_invariants.py` → `check_privacy_gate_usage()`

---

### Invariant 4: No-Content Logging

**Princip:**
- Inga payloads/headers/PII/content i logs
- Privacy guard ska skydda detta
- Endast metadata (counts, ids, format) i audit trails

**Implementation:**
- `privacy_guard.sanitize_for_logging()` används för all logging
- `privacy_guard.assert_no_content()` verifierar att inget content läcker
- Logs innehåller endast: request_id, status_code, latency, error_type (inte error_message med content)

**Verification:**
- `scripts/test_source_safety.py` (grep-regler)
- `make check-security-invariants` (statisk gate)

**Maskinläsbar check:** `scripts/check_security_invariants.py` → `check_no_content_in_logs()`

---

### Invariant 5: Fail-Closed Design

**Boot Fail Policy:**
- Systemet startar **INTE** om secrets saknas i `prod_brutal` (t.ex. `fernet_key` måste finnas i `/run/secrets/`)
- Systemet startar **INTE** om cloud API keys (t.ex. `OPENAI_API_KEY`) är satta i env i prod_brutal
- Systemet startar **INTE** om osäker konfiguration (t.ex. `SOURCE_SAFETY_MODE=false` i produktion)

**Runtime Fail-Closed:**
- Privacy Gate blockerar PII (422, ingen draft genereras)
- Egress guard blockerar externa requests (exception)
- mTLS blockerar unauthorized access (TLS handshake fails utan giltigt cert)

**Verification:**
- Startup checks (boot fail verification)
- Runtime checks (egress guard, Privacy Gate)

**Maskinläsbar check:** `scripts/check_security_invariants.py` → `check_no_cloud_keys_in_prod()`

---

## Säkerhetsarkitektur

### Network Architecture

```
Internet
   │
   │ (HTTPS + mTLS, port 443)
   ▼
[Proxy (Caddy)]
   │
   │ (HTTP over internal_net, port 8000)
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

---

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

---

## Secret Management

### Docker Secrets (prod_brutal)

**Princip:**
- I `prod_brutal` profile MÅSTE secrets komma från `/run/secrets/`
- Backend läser secrets från `/run/secrets/` (fallback till env endast i dev)
- Boot fail om secret saknas i `prod_brutal`

**Secrets:**
- `fernet_key` - Fernet encryption key (base64 URL-safe encoded)
- `PROJECT_FILES_KEY` - Project files encryption key (base64 URL-safe encoded)

**Key Management:**
- Rotera regelbundet
- Logga aldrig secrets
- Använd säker secrets manager (t.ex. Docker Swarm secrets, Kubernetes secrets)

---

## Certificate Lifecycle (mTLS)

### Client Certificates

**Princip:**
- Alla HTTPS-requests på 443 kräver giltigt klientcertifikat
- Utan cert: TLS handshake failar
- Certificate revocation support (CRL) är planerad men inte aktivt konfigurerad i nuvarande setup

**Setup:**
- Se arkiverad `docs/archive/2025-12/docs/MTLS_BROWSER_SETUP.md` för instruktioner om att installera client certifikat i webbläsare
- Testprofil kan användas för E2E-tester (separat cert-setup)

---

## Threat Model

### Hot

1. **Extern egress av känslig data**
   - **Mitigation:** Zero egress (infrastructure + code level)

2. **PII-leakage till externa AI:er**
   - **Mitigation:** Privacy Gate (obligatorisk maskning, fail-closed leak check)

3. **Unauthorized access**
   - **Mitigation:** mTLS enforcement (klientcertifikat krävs)

4. **Content leakage i logs**
   - **Mitigation:** No-content logging (privacy guard)

5. **Osäker konfiguration**
   - **Mitigation:** Fail-closed design (boot fail om osäker config)

---

## Verification & Testing

### Statisk Gate (CI)

```bash
make check-security-invariants
```

**Kör:**
- `check_no_egress_bypass()` - Inga direkta HTTP requests utan `ensure_egress_allowed()`
- `check_no_content_in_logs()` - Inga content/PII i log statements
- `check_mtls_required()` - Caddyfile kräver mTLS på port 443
- `check_zero_egress_network()` - Docker compose har `internal_net` med `internal: true`
- `check_no_cloud_keys_in_prod()` - Inga cloud API keys i prod_brutal env

**Om någon invariant bryts → CI failar → ändringen stoppas.**

### Runtime Gate

```bash
make verify-brutal
```

**Kör:**
- `scripts/verify_no_internet.sh` - Verifierar att backend inte kan nå internet
- `scripts/verify_mtls.sh` - Verifierar mTLS enforcement
- Startup checks - Verifierar fail-closed design

**Om någon invariant bryts → verifieringen failar → deployment stoppas.**

---

## Compliance & Regulatory

### GDPR

**Princip:**
- Krypterad lagring (Fernet encryption-at-rest)
- Retention policies (konfigurerbart per projekt)
- Secure deletion (best-effort overwrite + receipt)
- Inga filnamn/content i logs (privacy-safe logging)

**Detaljer:** Se [DATA_LIFECYCLE.md](./DATA_LIFECYCLE.md)

### Journalism Safety

**Princip:**
- Källskydd: Inga IP/user-agent/URL i logs (SOURCE_SAFETY_MODE)
- Original file is sacred: Original filename lagras INTE på disk
- Human-in-the-loop: Alla destruktiva handlingar kräver explicit confirm + reason

**Detaljer:** Se arkiverad `docs/archive/2025-12/docs/journalism-safety.md` (reference document)

---

## Referenser

- **System Overview:** [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
- **Data Lifecycle:** [DATA_LIFECYCLE.md](./DATA_LIFECYCLE.md)
- **AI Governance:** [AI_GOVERNANCE.md](./AI_GOVERNANCE.md)
- **Operational:** [OPERATIONAL_PLAYBOOK.md](./OPERATIONAL_PLAYBOOK.md)

---

## Maskinläsbar Säkerhet

Alla invariants är kodade i `scripts/check_security_invariants.py` och körs via:
- `make check-security-invariants` (statisk gate)
- `make verify-brutal` (runtime gate)

**Om en invariant bryts → verifieringen failar → ändringen stoppas.**

---

**Detta är en canonical document. Uppdatera endast om säkerhetsgarantier eller invariants ändras.**

