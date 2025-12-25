# AI Governance - Copy/Paste

**Version:** 1.0.0  
**Status:** Canonical Document (Single Source of Truth)  
**Senast uppdaterad:** 2025-12-25

---

## Syfte

Detta dokument definierar regler för AI-assistenter (t.ex. Cursor, GitHub Copilot) som arbetar i Copy/Paste-repot. Målet är att säkerställa att AI följer säkerhetsinvariants, håller kontext och inte bryter implicita regler.

---

## 🚫 HÅRDA REGLER FÖR DOKUMENTATION

**AI MAY NOT CREATE NEW DOCUMENTATION FILES**

**AI MUST UPDATE EXISTING CANONICAL DOCS ONLY**

**Regler:**
- ❌ Inga nya .md-filer får skapas utanför `docs/canonical/` och `docs/archive/`
- ❌ Inga "reference docs" får skapas
- ❌ Inga "summary"-filer får skapas
- ✅ Endast canonical docs i `docs/canonical/` får uppdateras
- ✅ Om ny information behövs: uppdatera relevant canonical doc

**Verifiering:** `make check-docs-integrity` failar om nya docs skapas

---

## Entry Point

**Alla AI-sessioner börjar här:**

1. Läs `docs/agent.md` (pekar på canonical docs)
2. Läs canonical docs i `docs/canonical/`:
   - [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md) - Vad systemet är
   - [SECURITY_MODEL.md](./SECURITY_MODEL.md) - Säkerhetsgarantier
   - [MODULE_MODEL.md](./MODULE_MODEL.md) - Hur moduler byggs
   - [DATA_LIFECYCLE.md](./DATA_LIFECYCLE.md) - Datahantering
   - [AI_GOVERNANCE.md](./AI_GOVERNANCE.md) (detta dokument) - AI-regler
   - [OPERATIONAL_PLAYBOOK.md](./OPERATIONAL_PLAYBOOK.md) - Drift

**Tid:** < 10 minuter för att förstå systemet

---

## Obligatoriska Dokument (MÅSTE läsas innan ändringar)

1. **`docs/agent.md`** - Entry point och konstitution
2. **`docs/canonical/SECURITY_MODEL.md`** - Exakt säkerhetssemantik
3. **`docs/canonical/MODULE_MODEL.md`** - Module Contract
4. **UI-stil:** Se arkiverad `docs/archive/2025-12/docs/UI_STYLE_TOKENS.md` (om UI ändras)

**Om du inte har läst dessa → LÄS DEM FÖRST innan du gör ändringar.**

---

## Hårda Invariants (FÅR INTE BRYTAS)

### 1. Zero Egress (prod_brutal)

- Backend ska **INTE** kunna nå internet via docker network
- `ensure_egress_allowed()` ska blockera alla externa providers i prod_brutal
- Boot fail om cloud API keys (t.ex. `OPENAI_API_KEY`) är satta i env i prod_brutal

**Verifiering:** `make check-security-invariants` → `check_zero_egress_network()`

### 2. mTLS Enforcement

- Alla HTTPS-requests på 443 kräver klientcertifikat
- Utan cert ska TLS-handshake faila
- Health/ready får endast vara åtkomligt på HTTP (80) för driftmonitoring

**Verifiering:** `make check-security-invariants` → `check_mtls_required()`

### 3. Privacy Gate

- Extern egress får endast ske med `MaskedPayload`
- Ingen raw text med PII får nå externa providers
- Leak => 422 (fail-closed)

**Verifiering:** `make check-privacy-gate` → `check_privacy_gate_usage()`

### 4. No-Content Logging

- Inga payloads/headers/PII/content i logs
- Privacy guard ska skydda detta
- Endast metadata (counts, ids, format) i audit trails

**Verifiering:** `make check-security-invariants` → `check_no_content_in_logs()`

### 5. Fail-Closed Design

- Osäker config i prod_brutal ska stoppa boot
- Exempel: `SOURCE_SAFETY_MODE=false` i produktion → boot fail
- Exempel: Cloud API keys satta i prod_brutal → boot fail

**Verifiering:** `make check-security-invariants` → `check_no_cloud_keys_in_prod()`

**Detaljer:** Se [SECURITY_MODEL.md](./SECURITY_MODEL.md)

---

## Arbetsregler (MÅSTE följas)

### Regel 1: Läs Först

**Innan du gör ändringar:**
1. Läs `docs/agent.md` (entry point)
2. Läs canonical docs i `docs/canonical/`
3. Läs relevanta modul-dokumentation (t.ex. `backend/app/modules/{module}/README.md`)

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
make check-security-invariants    # Statisk gate
make verify-brutal                # Runtime gate (om prod_brutal)
```

**Om du ändrar UI:**
```bash
cd frontend && npm run test:e2e   # E2E verifiering
```

### Regel 4: Uppdatera Dokumentation

**Om någon invariant behöver ändras:**
- Uppdatera `docs/canonical/SECURITY_MODEL.md` så att den exakt matchar implementationen
- UI↔API ändringar: Uppdatera relevant canonical doc (t.ex. SYSTEM_OVERVIEW.md för API-flöden)

### Regel 5: UI-standardisering

**Alla API-anrop i frontend MÅSTE gå via:**
- `frontend/src/api/client.ts` (request correlation + typed errors + mTLS detection)
- **Inga ad-hoc fetch-anrop i komponenter**

**UI-stil:**
- Behåll exakt enligt arkiverad `docs/archive/2025-12/docs/UI_STYLE_TOKENS.md`
- Ingen ny typography/färg/spacing utan tokens

---

## Security Impact Checklist

**Varje gång du gör en ändring som berör säkerhet, kontrollera:**

- [ ] Har jag läst `docs/canonical/SECURITY_MODEL.md`?
- [ ] Har jag kört `make check-security-invariants`?
- [ ] Har jag kört `make verify-brutal` (eller relevant verify-*)?
- [ ] Har jag uppdaterat `docs/canonical/SECURITY_MODEL.md` om semantik ändrats?
- [ ] Har jag uppdaterat relevant canonical doc om UI↔API ändrats?
- [ ] Använder alla API-anrop `frontend/src/api/client.ts`?
- [ ] Följer UI-stil enligt arkiverad `docs/archive/2025-12/docs/UI_STYLE_TOKENS.md`?

---

## Maskinläsbar Säkerhet

**Alla invariants är kodade i `scripts/check_security_invariants.py` och körs via:**
- `make check-security-invariants` (statisk gate)
- `make verify-brutal` (runtime gate)

**Om en invariant bryts → verifieringen failar → ändringen stoppas.**

**Detaljer:** Se [SECURITY_MODEL.md](./SECURITY_MODEL.md) → "Maskinläsbar Säkerhet"

---

## Superprompt

**För att säkerställa att olika AI-modeller följer samma regler, använd detta dokument (AI_GOVERNANCE.md) som startregel.**

**Template:**
```
Du arbetar i Copy/Paste-repot. Säkerhet är absolut. Följ dessa invariants och bevisa dem med körbara checks.

HÅRDA INVARIANTS (får inte brytas):
1. prod_brutal: zero egress. Backend ska inte kunna nå internet via docker network och ensure_egress_allowed() ska blockera alla externa providers.
2. mTLS: Alla HTTPS-requests på 443 kräver klientcertifikat (utan cert ska TLS-handshake faila). Health/ready får endast vara åtkomligt på HTTP (80) för driftmonitoring om det är så konfigurerat.
3. Privacy Gate: Extern egress får endast ske med MaskedPayload. Ingen raw text med PII får nå externa providers. Leak => 422.
4. No-content logging: inga payloads/headers/PII/content i logs. Privacy guard ska skydda detta.
5. Fail-closed: osäker config i prod_brutal ska stoppa boot (t.ex. SOURCE_SAFETY_MODE=false eller cloud API keys satta).

ARBETSSÄTT (måste följas):
A) Läs: docs/agent.md, docs/canonical/MODULE_MODEL.md (Module Contract), docs/canonical/SECURITY_MODEL.md.
B) Gör minsta möjliga ändring.
C) Kör verifiering och uppdatera evidenslogg:
   - make check-security-invariants
   - make verify-brutal (eller make verify-phase-b-runtime)
   - frontend: npm run test:e2e (relevant spec)
D) Om någon invariant behöver ändras: uppdatera docs/canonical/SECURITY_MODEL.md så att den exakt matchar implementationen.

OUTPUTKRAV:
- Ändra bara nödvändiga filer.
- Uppdatera relevant canonical doc när UI↔API ändras.
- Om du lägger till nya endpoints: lägg till E2E-test och uppdatera säkerhetsdokumentation om semantik påverkas.
- Alla API-anrop i frontend måste gå via frontend/src/api/client.ts (request correlation + typed errors). Inga ad-hoc fetch.
- Behåll UI-stil exakt enligt UI style tokens (ingen ny typography/färg/spacing utan tokens).
```

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
2. **Läs `docs/canonical/SECURITY_MODEL.md`** först
3. **Kör `make verify-brutal`** för att se vad som kan påverkas
4. **Om du fortfarande är osäker → dokumentera osäkerheten** i en issue eller kommentar

**Hellre nere än osäkert.**

---

## Snabbreferens

**Läs först:**
- `docs/agent.md` (entry point)
- `docs/canonical/SECURITY_MODEL.md`
- `docs/canonical/MODULE_MODEL.md`
- `docs/archive/2025-12/docs/UI_STYLE_TOKENS.md` (om UI ändras)

**Kör alltid:**
- `make check-security-invariants` (statisk gate)
- `make verify-brutal` (runtime gate)

**Uppdatera alltid:**
- `docs/canonical/SECURITY_MODEL.md` (om semantik ändras)
- Relevant canonical doc (om UI↔API ändras)

**Använd alltid:**
- `frontend/src/api/client.ts` (för alla API-anrop)
- `docs/archive/2025-12/docs/UI_STYLE_TOKENS.md` (för UI-stil)

---

## Referenser

- **System Overview:** [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
- **Security Model:** [SECURITY_MODEL.md](./SECURITY_MODEL.md)
- **Module Model:** [MODULE_MODEL.md](./MODULE_MODEL.md)
- **Data Lifecycle:** [DATA_LIFECYCLE.md](./DATA_LIFECYCLE.md)
- **Operational:** [OPERATIONAL_PLAYBOOK.md](./OPERATIONAL_PLAYBOOK.md)

---

**Detta är en canonical document. Uppdatera endast om AI-governance-regler ändras.**

