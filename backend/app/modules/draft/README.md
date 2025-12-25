# Draft Module

**Modul:** `app.modules.draft`

**Ansvar:** Event-based draft generation med Privacy Gate enforcement.

**Status:** ✅ Implementerad, följer Module Contract v1

---

## Purpose

Draft-modulen genererar drafts för events med **obligatorisk Privacy Gate enforcement**. All text måste passera genom `privacy_gate.ensure_masked_or_raise()` innan någon extern LLM kan användas.

---

## API Contract

### POST /api/v1/events/{event_id}/draft

Skapa draft för event.

**Request:**
```json
{
  "raw_text": "string",
  "mode": "strict|balanced"
}
```

**Response (201 Created):**
```json
{
  "draft_id": 1,
  "event_id": 1,
  "content": "Generated draft...",
  "created_at": "2025-12-24T12:00:00"
}
```

**Response (422 PII Detected):**
```json
{
  "error": {
    "code": "pii_detected",
    "message": "PII detected in input - draft generation blocked",
    "request_id": "uuid"
  }
}
```

---

## Privacy Gate Enforcement

**CRITICAL:** All text MÅSTE passera Privacy Gate innan draft generation:

```python
# STEP 1: Privacy Gate (OBLIGATORY - no bypass possible)
masked_payload = await ensure_masked_or_raise(
    text=request_body.raw_text,
    mode=request_body.mode or "strict",
    request_id=request_id
)

# STEP 2: Create draft using masked text only
draft = await create_draft(
    event_id=event_id,
    masked_text=masked_payload.text,  # Only masked text (no raw PII)
    request_id=request_id
)
```

---

## Data Handling

### Vad vi lagrar:
- Draft content (genererad från masked text)
- Event ID
- Created timestamp

### Vad vi ALDRIG lagrar/loggar:
- ❌ Raw input text (endast masked text någonsin nås av draft service)
- ❌ PII-värden
- ❌ Headers/payloads
- ❌ `str(e)` i produktion

---

## Security

### Privacy Protection

- **Privacy Gate enforcement:** Obligatorisk maskning innan draft generation
- **Fail-closed design:** 422 om PII detekteras (ingen draft genereras)
- **Masked text only:** Draft service accepterar endast masked text (garanti via type system)

### Error Handling

- **422 pii_detected:** Privacy Gate blockerade request (logga endast error_type + request_id)
- **404 event_not_found:** Event saknas (normal error handling)
- **500 internal_error:** Oväntat fel (logga endast error_type)

---

## Testing

### Privacy Chain Test

```bash
make verify-privacy-chain
```

Testar att:
1. Draft med PII → 422 pii_detected (blockeras)
2. Draft med safe text → 201/404 (accepteras eller event saknas)

---

## Provider Abstraction

Draft-modulen använder provider-abstraktion för externa LLM:er:

- **Stub Provider:** Placeholder implementation (ingen extern LLM än)
- **Future:** OpenAI provider kommer integreras via `privacy_gate` + `MaskedPayload`

Alla providers MÅSTE:
- Acceptera endast masked text (eller `MaskedPayload`)
- Vara placerade i `app/modules/draft/providers/`
- Följa Privacy Gate enforcement

---

## Module Contract Compliance

✅ Följer Module Contract v1:
- ✅ Importerar endast tillåtna core-moduler (config, logging)
- ✅ Privacy-safe logging (ingen PII, payloads, headers, paths)
- ✅ Error handling med request_id
- ✅ Dokumentation (denna README)

---

## Relaterade Dokument

- [Privacy Gate](docs/privacy-gate.md)
- [Privacy Shield Module](../privacy_shield/README.md)

