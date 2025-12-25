# Module Model - Copy/Paste

**Version:** 1.0.0  
**Status:** Canonical Document (Single Source of Truth)  
**Senast uppdaterad:** 2025-12-25

---

## Vad är en Modul?

En modul är en **självständig feature** som levererar specifik funktionalitet (t.ex. Record, Transcripts, Projects). Alla moduler följer **Module Contract v1** och är isolerade från CORE.

### Modulstruktur

```
backend/app/modules/{module_name}/
├── __init__.py          # Module exports
├── models.py            # SQLAlchemy models (om DB behövs)
├── router.py            # FastAPI router (endpoints)
├── service.py           # Business logic
├── schemas.py           # Pydantic schemas (request/response)
├── README.md            # Module-specifik dokumentation
└── tests/               # Module-specifika tester (valfritt)
```

---

## Module Contract v1

### Regel 1: CORE är Frozen

**CORE (`backend/app/core/`) får INTE ändras av moduler.**

**Tillåtna imports från CORE:**
- `app.core.logging` - Logger (privacy-safe)
- `app.core.config` - Settings (read-only)
- `app.core.database` - `get_db()` context manager (om DB behövs)
- `app.core.errors` - Error response helpers (valfritt)

**Förbjudna imports:**
- `app.core.middleware` - Middleware är CORE-intern
- `app.core.lifecycle` - Lifecycle är CORE-intern
- Direkta ändringar i CORE-filer

**Rationale:** CORE är fundamentet. Om CORE ändras, påverkar det alla moduler. Därför är CORE frozen och ändras endast vid kritiska säkerhetsfixar eller arkitektoniska förändringar.

---

### Regel 2: Router Registration

**Varje modul registrerar sin router i `app/main.py`:**

```python
# backend/app/main.py
from app.modules.record.router import router as record_router

app.include_router(record_router, prefix="/api/v1/record", tags=["record"])
```

**Router-struktur:**
- Prefix: `/api/v1/{module_name}`
- Tags: `[{module_name}]` (för Swagger UI)
- Endpoints: RESTful (GET, POST, PATCH, DELETE)

---

### Regel 3: Privacy-Safe Logging

**Alla log statements måste vara privacy-safe:**

```python
# ✅ RÄTT
from app.core.logging import logger

logger.info(
    "record_created",
    extra={
        "record_id": record_id,
        "size_bytes": size_bytes,
        "mime_type": mime_type,
        # INGA filnamn, content, PII
    }
)

# ❌ FEL
logger.info(f"Created record: {filename}")  # Filnamn i log
logger.info(f"Content: {file_content}")     # Content i log
```

**Använd `privacy_guard.sanitize_for_logging()` om osäker:**
```python
from app.core.privacy_guard import sanitize_for_logging

safe_data = sanitize_for_logging(data)
logger.info("event", extra=safe_data)
```

**Verification:** `make check-security-invariants` → `check_no_content_in_logs()`

---

### Regel 4: DB-Optional Design

**Moduler ska fungera även om DB saknas:**

```python
from app.core.database import get_db, engine
from app.core.config import settings

def _has_db() -> bool:
    """Check if database is available."""
    return engine is not None and settings.database_url is not None

def some_endpoint():
    if not _has_db():
        raise HTTPException(
            status_code=503,
            detail={
                "status": "db_uninitialized",
                "message": "Database not available",
            }
        )
    # ... rest of logic
```

**Rationale:** Backend ska starta även om DB är nere. Moduler som kräver DB ska returnera tydliga fel (503 med `db_uninitialized` eller `db_down`).

---

### Regel 5: Dokumentation

**Varje modul MÅSTE ha en `README.md` med:**

1. **Översikt:** Vad modulen gör
2. **Endpoints:** Lista över alla endpoints med request/response exempel
3. **Models:** DB-modeller (om DB används)
4. **Security:** Säkerhetsaspekter (kryptering, privacy, etc.)
5. **Testing:** Hur man testar modulen

**Exempel:** Se `backend/app/modules/example/README.md` (reference implementation)

---

## Tillåtna Beroenden

### Modul → CORE

✅ **Tillåtet:**
- `app.core.logging` - Logger
- `app.core.config` - Settings
- `app.core.database` - DB access
- `app.core.errors` - Error helpers
- `app.core.privacy_guard` - Privacy utilities
- `app.core.file_storage` - File storage utilities (om tillgängligt)

### Modul → Modul

⚠️ **Varning:** Moduler ska vara självständiga. Cross-module dependencies ska minimeras.

**Tillåtet (med försiktighet):**
- Modul A kan importera Modul B:s models (t.ex. `Project` från `projects` modulen)
- Modul A kan anropa Modul B:s service functions (t.ex. `privacy_shield.mask_text()`)

**Förbjudet:**
- Circular dependencies (Modul A → Modul B → Modul A)
- Tight coupling (Modul A kräver Modul B för att fungera)

**Rationale:** Moduler ska kunna utvecklas och testas oberoende. Tight coupling gör systemet svårt att underhålla.

---

## Exempel: Reference Implementation

**Se `backend/app/modules/example/README.md` för komplett exempel.**

**Kort sammanfattning:**
1. Router definierar endpoints
2. Service innehåller business logic
3. Models definierar DB-struktur (om DB behövs)
4. Schemas definierar request/response-typer
5. README dokumenterar allt

---

## Säkerhetsaspekter

### Privacy-Safe Logging

**Alla moduler måste följa no-content logging:**
- Inga filnamn i logs
- Inga content/PII i logs
- Endast metadata (counts, ids, format)

**Verification:** `make check-security-invariants` → `check_no_content_in_logs()`

### Encryption-at-Rest

**Om modulen lagrar filer:**
- Använd `app.core.file_storage` (eller motsvarande)
- Kryptera innan lagring (Fernet)
- Lagra som `{sha256}.bin` (inte original filename)
- Original filename: Endast i DB (aldrig på disk)

**Exempel:** Se `backend/app/modules/projects/file_storage.py`

### Egress Control

**Om modulen gör externa anrop:**
- Måste kalla `ensure_egress_allowed()` innan anrop
- Måste passera Privacy Gate (om raw text skickas)
- Använd `MaskedPayload` för externa LLM-anrop

**Verification:** `make check-security-invariants` → `check_no_egress_bypass()`

---

## Testing

### Unit Tests

**Placering:** `backend/app/modules/{module_name}/tests/` (valfritt)

**Struktur:**
- Testa service functions
- Testa router endpoints (mock DB)
- Testa säkerhetsaspekter (privacy, encryption)

### Integration Tests

**Placering:** `scripts/test_*.py` eller `tests/`

**Struktur:**
- Testa end-to-end flows
- Testa mot riktig DB (om möjligt)
- Testa säkerhetsgarantier (zero egress, mTLS, Privacy Gate)

---

## Referenser

- **System Overview:** [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
- **Security Model:** [SECURITY_MODEL.md](./SECURITY_MODEL.md)
- **Data Lifecycle:** [DATA_LIFECYCLE.md](./DATA_LIFECYCLE.md)
- **AI Governance:** [AI_GOVERNANCE.md](./AI_GOVERNANCE.md)

---

**Detta är en canonical document. Uppdatera endast om Module Contract ändras.**

