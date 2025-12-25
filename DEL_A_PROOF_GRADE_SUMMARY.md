# DEL A - Proof-Grade Validation Summary

**Datum:** 2025-12-24  
**Status:** ✅ STATISK VALIDATION GODKÄND | ⏳ RUNTIME VALIDATION PENDING

---

## ✅ Statisk Validation (Config Correctness)

### Förbättrad `validate_del_a.sh`:

1. **Robust Backend Port Check:**
   - Använder section-scan (awk) istället för enkel grep
   - Verifierar explicit att `ports:` INTE finns i backend-sektionen
   - ✅ PASS - Backend har ingen ports-sektion

2. **Network Verification:**
   - Verifierar `internal_net` med `internal: true`
   - Kontrollerar att backend endast är på `internal_net` (inte `default`)
   - ✅ PASS - Backend isolerad på internal_net

3. **Caddyfile mTLS:**
   - Verifierar `client_auth` och `require_and_verify`
   - ✅ PASS - mTLS korrekt konfigurerad

4. **Scripts:**
   - Syntax validation: ✅
   - Permissions: ✅

**Resultat:** ✅ ALL STATIC TESTS PASSED

---

## ⏳ Runtime Validation (Proof-Grade)

### Ny `validate_del_a_runtime.sh`:

**Krav:** Stack måste köras (`docker-compose -f docker-compose.prod_brutal.yml up -d`)

**Test 1: mTLS Runtime Verification**
- Kör `scripts/verify_mtls.sh`
- Förväntat:
  - ❌ Request utan cert → 403
  - ✅ Request med cert → 200

**Test 2: No Internet Access**
- Kör `scripts/verify_no_internet.sh` INNANFÖR backend container
- Förväntat:
  - ❌ DNS lookup → fail
  - ❌ HTTP request → fail
  - ❌ Ping → fail

### Ny `scripts/verify_no_internet.sh`:

Testar från INNANFÖR backend container:
- DNS lookup (nslookup google.com)
- HTTP request (curl https://www.google.com)
- Ping (ping 8.8.8.8)

Alla ska FAILA om backend verkligen är isolerad.

---

## 🎯 `make verify-brutal` Target

Kör både statisk + runtime validering:

```bash
make verify-brutal
```

**Steg:**
1. Statisk validering (config correctness) - `validate_del_a.sh`
2. Runtime validering (proof-grade) - `validate_del_a_runtime.sh`

**Förutsättningar för runtime:**
- Certifikat genererade: `./scripts/generate_certs.sh`
- Stack körs: `docker-compose -f docker-compose.prod_brutal.yml up -d`

---

## Status

### ✅ KLART:
- Statisk validering förbättrad och godkänd
- Runtime validation scripts skapade
- `make verify-brutal` target tillagt

### ⏳ PENDING:
- Runtime tester måste köras när stack är igång
- mTLS runtime test (403 utan cert, 200 med cert)
- No-internet runtime test (från backend container)

---

## Nästa Steg

1. **Generera certifikat:**
   ```bash
   ./scripts/generate_certs.sh
   ```

2. **Starta brutal stack:**
   ```bash
   docker-compose -f docker-compose.prod_brutal.yml up -d
   ```

3. **Kör full validering:**
   ```bash
   make verify-brutal
   ```

4. **När runtime-tester passerar:**
   - ✅ DEL A är "proof-grade" validerad
   - ✅ Bunker-status bekräftad
   - ✅ Redo för DEL B

---

## Noteringar

- Statisk validering är **oberoende av Docker** (bara fil-läsning)
- Runtime validering **kräver** att stacken körs
- `verify_no_internet.sh` måste köras INNANFÖR container (via docker exec)
- mTLS test kräver att certifikat är genererade

