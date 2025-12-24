# Autonomy Guard Module

**Modul:** `app.modules.autonomy_guard`

**Ansvar:** Guardrails för att förhindra autonoma handlingar utan mänsklig granskning.

**Status:** ✅ Aktiv, registrerad i `main.py`

---

## Structure

```
backend/app/modules/autonomy_guard/
├── __init__.py
├── router.py          # FastAPI router
└── checks.py          # Guard check logic
```

---

## Endpoints

### POST /api/v1/autonomy/check

Kontrollera om en handling tillåts enligt autonomy guard policies.

**Request:**
```json
{
  "action": "publish" | "delete" | "export",
  "context": {}
}
```

**Response:**
```json
{
  "allowed": true | false,
  "reason": "Explanation"
}
```

---

## Purpose

Autonomy Guard säkerställer att kritiska handlingar (publish, delete, export) kräver mänsklig granskning och inte kan utföras autonomt.

---

## Module Contract Compliance

- ✅ **Core Imports:** Endast `app.core.logging` och `app.core.config`
- ✅ **Router Registration:** Registrerad i `app/main.py` med prefix `/api/v1/autonomy`
- ✅ **Privacy-Safe Logging:** Använder structured logging, ingen PII i logs
- ✅ **No DB Requirements:** Ingen database dependency

---

## Testing

Modulen testas via:
- Integration tests i `make test`

**Notera:** Detaljerad implementation finns i `checks.py`. Se filen för mer information.

