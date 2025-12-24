# Privacy Shield Module

**Modul:** `app.modules.privacy_shield`

**Ansvar:** Defense-in-depth PII masking för externa LLM-egress. Garantierar att ingen råtext med direktidentifierande PII kan skickas till externa API:er (OpenAI, etc.).

**Status:** ✅ Implementerad, följer Module Contract v1

---

## Structure

```
backend/app/modules/privacy_shield/
├── __init__.py
├── router.py              # FastAPI router (POST /api/v1/privacy/mask)
├── service.py             # Pipeline + policy (defense-in-depth)
├── models.py              # Pydantic request/response + MaskedPayload type
├── regex_mask.py          # Baseline masking + entity counts
├── leak_check.py          # Blocking preflight check
├── providers/
│   ├── openai_provider.py # Hard gate (only MaskedPayload)
│   └── llamacpp_provider.py # Advisory control check
├── tests/
│   └── test_privacy_shield.py  # 30+ test cases
└── README.md
```

---

## Purpose

Privacy Shield är en **fail-closed, defense-in-depth** modul som säkerställer att:

1. **Ingen råtext med PII** kan skickas till externa LLM:er (OpenAI, etc.)
2. **All extern egress** måste gå via en enda provider-wrapper med hard gate
3. **Type-safe garantier**: Externa providers accepterar endast `MaskedPayload`, aldrig raw `str`
4. **Multi-layer masking**: Baseline regex → leak check → control check (advisory)

---

## Data Handling

### Vad vi lagrar:
- **Ingen text lagras** - all bearbetning sker in-memory
- **Metadata loggas**: request_id, provider, mode, latency_ms, error_type, error_code
- **Entity counts**: Antal hittade entiteter per kategori (persons, orgs, locations, contacts, ids)

### Vad vi ALDRIG lagrar/loggar:
- ❌ Text-innehåll (varken input eller output)
- ❌ Tokens/spans
- ❌ Mapping (token → real name)
- ❌ PII-värden
- ❌ Headers/payloads
- ❌ `str(e)` i produktion (endast `error_type`)

---

## API Contract

### POST /api/v1/privacy/mask

Maskera PII i text med defense-in-depth pipeline.

**Request:**
```json
{
  "text": "string",
  "mode": "strict|balanced",
  "language": "sv",
  "context": {"eventId": "...", "sourceType": "..."}
}
```

**Response:**
```json
{
  "maskedText": "string",
  "summary": null,
  "entities": {
    "persons": 0,
    "orgs": 0,
    "locations": 0,
    "contacts": 0,
    "ids": 0
  },
  "privacyLogs": [
    {"rule": "EMAIL", "count": 1},
    {"rule": "PHONE", "count": 1}
  ],
  "provider": "regex|llamacpp",
  "requestId": "uuid",
  "control": {
    "ok": true,
    "reasons": []
  }
}
```

**Error Responses:**
- `413`: Input text exceeds `PRIVACY_MAX_CHARS`
- `422`: Privacy leak detected (PII kvar efter maskning)
- `500`: Internal error

---

## Pipeline (Defense-in-Depth)

### A) Baseline Mask (MÅSTE alltid köras)

Maskerar minst:
- Email (`test@example.com` → `[EMAIL]`)
- Telefon (`070-123 45 67` → `[PHONE]`)
- Svenskt personnummer (`800101-1234` → `[PNR]`)
- ID-liknande mönster (`ABC123DEF456` → `[ID]`)
- Postnummer (`12345` → `[POSTCODE]`)
- Adress (`Gatan 123` → `[ADDRESS]`)

Räknar entities per kategori och skapar privacy logs.

### B) Leak Check (BLOCKERANDE)

Kör regex-detektorer igen på `maskedText`.

Om någon träff kvar → `PrivacyLeakError` (error_code="privacy_leak_detected"):
- **strict mode**: Gör en extra aggressiv re-mask och kör leak-check igen
- Om fortfarande läckage → 422 med generiskt fel + request_id

### C) Control Check (ADVISORY, strict mode only)

Om `LLAMACPP_BASE_URL` finns:
- Kör `control_check(maskedText)` via llama.cpp `/v1/chat/completions`
- **balanced mode**: Control check är icke-blockerande
- **strict mode**: Om control_check säger NOT OK → applicera extra maskning (konservativt) och leak-check igen
- Om fortfarande fail → 422

### D) External Egress Hard Gate

**MaskedPayload-modell:**
- Endast Privacy Shield kan skapa den (type-safe)
- `openai_provider.py` får endast acceptera `MaskedPayload`, aldrig `str`
- `openai_provider.py` kör `leak_check()` preflight innan nätverkscall
- Om leak_check failar → abort innan call (ingen extern request)

---

## Guarantees

### Format PII Leak-Check Guarantee

**Efter maskning garanterar vi:**
- `maskedText` innehåller endast tokens (`[EMAIL]`, `[PHONE]`, etc.)
- `leak_check()` hittar 0 direktidentifierande PII efter maskning
- Om leak_check failar → request blockeras (422)

### Fail-Closed Behavior

1. **Input validation**: Text > `PRIVACY_MAX_CHARS` → 413 (ingen truncation)
2. **Leak detection**: Om PII kvar efter maskning → 422 (request blockeras)
3. **Provider gate**: OpenAI-provider kräver `ALLOW_EXTERNAL=true` OCH `OPENAI_API_KEY`
4. **Preflight check**: OpenAI-provider kör leak_check() innan API-call (ingen request om leak)

### Type Safety

- `MaskedPayload` kan endast skapas av Privacy Shield service
- Externa providers (OpenAI) accepterar endast `MaskedPayload` (type-level guarantee)
- Test: `openai_provider.generate(masked_payload: MaskedPayload)` - kan inte anropas med `str`

---

## Config/Env

**Settings (i `app.core.config.Settings`):**

```python
# LLaMA.cpp control model (optional)
LLAMACPP_BASE_URL: Optional[str] = None  # e.g., "http://localhost:8080"

# External API gate
ALLOW_EXTERNAL: bool = False  # Must be True for OpenAI provider
OPENAI_API_KEY: Optional[str] = None

# Limits
PRIVACY_MAX_CHARS: int = 50000  # Max input length (413 if exceeded)
PRIVACY_TIMEOUT_SECONDS: int = 10  # Timeout for external calls
```

**Start-gate:**
- Om `OPENAI_API_KEY` är satt men `ALLOW_EXTERNAL` inte är `true` → logga varning och håll `openai_provider` inaktiv

---

## Limitations

### Implicit Identifiers

Privacy Shield fokuserar på **direktidentifierande PII** (email, telefon, personnummer, etc.).

**Vad som INTE maskeras:**
- Implicita identifierare (t.ex. "kändis från TV", "politiker i Stockholm")
- Kontextuell information som kan identifiera (t.ex. unika jobbtitlar + plats)
- Semantisk information (t.ex. "person som jobbar på X och bor på Y")

**Rationale:**
- Regex-baserad masking fokuserar på strukturerad PII
- För semantisk anonymisering krävs mer avancerade modeller (framtida utveckling)

---

## How to Run LLaMA.cpp Control Model

**För att använda control check (advisory, strict mode):**

1. Starta LLaMA.cpp med OpenAI-compatible API:
   ```bash
   llama-server --host 0.0.0.0 --port 8080
   ```

2. Sätt env var:
   ```bash
   LLAMACPP_BASE_URL=http://localhost:8080
   ```

3. Control check körs automatiskt i strict mode (advisory, icke-blockerande i balanced mode)

---

## Testing

**Kör tester:**
```bash
cd backend
pytest app/modules/privacy_shield/tests/test_privacy_shield.py -v
```

**Test coverage (30+ cases):**
- ✅ Email masking (olika format)
- ✅ Telefon masking (olika format)
- ✅ Personnummer masking (olika format)
- ✅ Postnummer masking
- ✅ Adress masking
- ✅ ID-liknande mönster
- ✅ Kombinationer av PII
- ✅ Unicode-stöd
- ✅ Whitespace-hantering
- ✅ Case-insensitive matching
- ✅ Leak check (no leaks after masking)
- ✅ Leak detection (raises PrivacyLeakError)
- ✅ API endpoints (success cases)
- ✅ API endpoints (error cases: too large, leaks)
- ✅ MaskedPayload type safety
- ✅ Edge cases (empty text, no PII, special chars, newlines)

**Verifiera:**
- `maskedText` innehåller tokens
- `leak_check` hittar 0 efter maskning
- OpenAI-provider kan inte anropas med raw text (type-level + test spy)

---

## Module Contract Compliance

### Allowed Core Imports ✅

Modulen använder endast tillåtna core-imports:
- `app.core.logging` (logger) - för privacy-safe logging
- `app.core.config` (settings) - för konfiguration

### Router Registration ✅

Registrerad i `app/main.py`:
```python
from app.modules.privacy_shield.router import router as privacy_shield_router
app.include_router(privacy_shield_router, prefix="/api/v1/privacy", tags=["privacy"])
```

### Privacy-Safe Logging ✅

All logging följer privacy-policy:
```python
logger.info("privacy_mask_complete", extra={
    "request_id": request_id,
    "mode": request_body.mode,
    "provider": "regex",
    "latency_ms": 123.45
})
```

- ✅ Inga payloads loggas
- ✅ Inga headers loggas
- ✅ Inga paths loggas
- ✅ Endast `error_type`, aldrig `str(e)`

### Error Handling ✅

- Använder FastAPI `HTTPException` för fel
- Global exception handlers hanterar dem automatiskt
- `PrivacyLeakError` fångas och returneras som 422

### Database ✅

- Inga DB-models
- DB-optional: Modulen fungerar utan DB

---

## Usage Example

**Mask text:**
```bash
curl -X POST http://localhost:8000/api/v1/privacy/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Kontakta mig på test@example.com eller ring 070-123 45 67",
    "mode": "balanced",
    "language": "sv"
  }'
```

**Response:**
```json
{
  "maskedText": "Kontakta mig på [EMAIL] eller ring [PHONE]",
  "summary": null,
  "entities": {
    "persons": 0,
    "orgs": 0,
    "locations": 0,
    "contacts": 2,
    "ids": 0
  },
  "privacyLogs": [
    {"rule": "EMAIL", "count": 1},
    {"rule": "PHONE", "count": 1}
  ],
  "provider": "regex",
  "requestId": "abc-123-def",
  "control": {"ok": true, "reasons": []}
}
```

---

## GDPR Summary

**Privacy Shield garanterar:**
- ✅ Inga rå PII-värden skickas till externa API:er
- ✅ Type-safe garantier (`MaskedPayload` endast)
- ✅ Fail-closed beteende (blockerar vid läckage)
- ✅ Privacy-safe logging (ingen text, endast metadata)
- ✅ Defense-in-depth (multi-layer masking + leak check)

**Vad vi INTE garanterar:**
- ⚠️ Semantisk anonymisering (implicita identifierare)
- ⚠️ Kontextuell anonymisering (unika kombinationer)

