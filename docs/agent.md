# Agent Konstitution - Copy/Paste

**Detta dokument är OBLIGATORISK läsning för alla AI-assistenter som arbetar i detta repo.**

## Huvudregel

**Säkerhet är absolut. Inga undantag. Inga kompromisser.**

Om du är osäker på om en ändring påverkar säkerheten → **STOPPA OCH FRÅGA** eller läs `docs/security-complete.md` först.

---

## Obligatoriska Dokument (MÅSTE läsas innan ändringar)

1. **`docs/agent.md`** (detta dokument) - Konstitution och arbetsregler
2. **`docs/security-complete.md`** - Exakt säkerhetssemantik och implementation
3. **`docs/core.md`** - Module Contract och backend-regler
4. **`docs/UI_STYLE_TOKENS.md`** - UI-stil lås (ingen ny design utan tokens)

**Om du inte har läst dessa → LÄS DEM FÖRST innan du gör ändringar.**

---

## Hårda Invariants (FÅR INTE BRYTAS)

### 1. Zero Egress (prod_brutal)
- Backend ska **INTE** kunna nå internet via docker network
- `ensure_egress_allowed()` ska blockera alla externa providers i prod_brutal
- Boot fail om cloud API keys (t.ex. `OPENAI_API_KEY`) är satta i env i prod_brutal

**Verifiering:** `make verify-brutal` eller `scripts/verify_no_internet.sh`

### 2. mTLS Enforcement
- Alla HTTPS-requests på 443 kräver klientcertifikat
- Utan cert ska TLS-handshake faila
- Health/ready får endast vara åtkomligt på HTTP (80) för driftmonitoring

**Verifiering:** `scripts/verify_mtls.sh` eller `make verify-brutal`

### 3. Privacy Gate
- Extern egress får endast ske med `MaskedPayload`
- Ingen raw text med PII får nå externa providers
- Leak => 422 (fail-closed)

**Verifiering:** `make verify-privacy-chain` eller `make check-privacy-gate`

### 4. No-Content Logging
- Inga payloads/headers/PII/content i logs
- Privacy guard ska skydda detta
- Endast metadata (counts, ids, format) i audit trails

**Verifiering:** `scripts/test_source_safety.py` eller grep-regler

### 5. Fail-Closed Design
- Osäker config i prod_brutal ska stoppa boot
- Exempel: `SOURCE_SAFETY_MODE=false` i produktion → boot fail
- Exempel: Cloud API keys satta i prod_brutal → boot fail

**Verifiering:** Startup checks och `make verify-brutal`

---

## Arbetsregler (MÅSTE följas)

### Regel 1: Läs Först
**Innan du gör ändringar:**
1. Läs `docs/agent.md` (detta dokument)
2. Läs `docs/core.md` (Module Contract)
3. Läs `docs/security-complete.md` (säkerhetssemantik)
4. Läs `docs/UI_STYLE_TOKENS.md` (om du ändrar UI)

### Regel 2: Gör Minsta Möjliga Ändring
- Ändra bara nödvändiga filer
- Inga stora refactorings på en gång
- Små, verifierade commits

### Regel 3: Verifiera Alltid
**Efter varje ändring som berör:**
- Routes/endpoints
- Caddyfile / compose
- Providers/network
- Logging/middleware
- Storage/retention
- UI API-anrop

**Måste du köra:**
```bash
make check-privacy-gate    # Statisk gate (förhindrar fel kod)
make verify-brutal         # Runtime gate (förhindrar fel driftsättning)
```

**Om du ändrar UI:**
```bash
cd frontend && npm run test:e2e  # E2E verifiering
```

### Regel 4: Uppdatera Dokumentation
**Om någon invariant behöver ändras:**
- Uppdatera `docs/security-complete.md` så att den exakt matchar implementationen
- Uppdatera `docs/UI_API_INTEGRATION_REPORT.md` när UI↔API ändras
- Logga evidens i `docs/UI_E2E_RUNLOG.md` eller liknande

### Regel 5: UI-standardisering
**Alla API-anrop i frontend MÅSTE gå via:**
- `frontend/src/api/client.ts` (request correlation + typed errors + mTLS detection)
- **Inga ad-hoc fetch-anrop i komponenter**

**UI-stil:**
- Behåll exakt enligt `docs/UI_STYLE_TOKENS.md`
- Ingen ny typography/färg/spacing utan tokens

---

## Security Impact Checklist

**Varje gång du gör en ändring som berör säkerhet, kontrollera:**

- [ ] Har jag läst `docs/security-complete.md`?
- [ ] Har jag kört `make check-privacy-gate`?
- [ ] Har jag kört `make verify-brutal` (eller relevant verify-*)?
- [ ] Har jag uppdaterat `docs/security-complete.md` om semantik ändrats?
- [ ] Har jag uppdaterat `docs/UI_API_INTEGRATION_REPORT.md` om UI↔API ändrats?
- [ ] Har jag loggat evidens i `docs/UI_E2E_RUNLOG.md`?
- [ ] Använder alla API-anrop `frontend/src/api/client.ts`?
- [ ] Följer UI-stil `docs/UI_STYLE_TOKENS.md`?

---

## Output-krav

**När du levererar ändringar:**

1. **Ändra bara nödvändiga filer**
2. **Uppdatera dokumentation** om semantik påverkas
3. **Lägg till E2E-test** om du lägger till nya endpoints
4. **Kör verifiering** och visa resultat
5. **Behåll UI-stil** exakt enligt tokens

---

## Om Du Är Osäker

**Om du är osäker på om en ändring påverkar säkerheten:**

1. **STOPPA**
2. **Läs `docs/security-complete.md`** först
3. **Kör `make verify-brutal`** för att se vad som kan påverkas
4. **Om du fortfarande är osäker → dokumentera osäkerheten** i en issue eller kommentar

**Hellre nere än osäkert.**

---

## Snabbreferens

**Läs först:**
- `docs/agent.md` (detta dokument)
- `docs/security-complete.md`
- `docs/core.md`
- `docs/UI_STYLE_TOKENS.md`

**Kör alltid:**
- `make check-privacy-gate` (statisk gate)
- `make verify-brutal` (runtime gate)

**Uppdatera alltid:**
- `docs/security-complete.md` (om semantik ändras)
- `docs/UI_API_INTEGRATION_REPORT.md` (om UI↔API ändras)

**Använd alltid:**
- `frontend/src/api/client.ts` (för alla API-anrop)
- `docs/UI_STYLE_TOKENS.md` (för UI-stil)

---

**Detta är en levande dokument. Uppdatera den när nya regler läggs till.**

