# Console Module

**Modul:** `app.modules.console`

**Ansvar:** Events och Sources endpoints för frontend UI (Console/Pipeline/Sources-vyer).

**Status:** ✅ Implementerad, följer Module Contract v1

---

## Structure

```
backend/app/modules/console/
├── __init__.py
├── router.py          # FastAPI router (events & sources endpoints)
└── README.md          # Module documentation
```

---

## Endpoints

### GET /api/v1/events

Lista events för Console/Pipeline-vyn.

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-here",
      "title": "Event title",
      "summary": "Event summary",
      "source": "TT Flash",
      "sourceType": "RSS",
      "timestamp": "2025-12-24T10:00:00",
      "status": "INKOMMANDE",
      "score": 95,
      "isDuplicate": false
    }
  ],
  "total": 10,
  "limit": 50
}
```

**Datakällor:**
- In-memory store (`privacy_service._event_store`)
- Scout dedupe_store (om tillgänglig)

**Fallback:**
- Returnerar tom lista om DB inte är konfigurerad
- Returnerar tom lista om scout inte är tillgänglig

### GET /api/v1/events/{event_id}

Hämta specifik event.

**Response:**
```json
{
  "id": "uuid-here",
  "title": "Event title",
  "summary": "Event summary",
  "source": "TT Flash",
  "sourceType": "RSS",
  "timestamp": "2025-12-24T10:00:00",
  "status": "INKOMMANDE",
  "score": 95,
  "content": "...",
  "isDuplicate": false
}
```

### GET /api/v1/sources

Lista sources/feeds för Sources-vyn.

**Response:**
```json
{
  "items": [
    {
      "id": "src-abc123",
      "name": "TT Flash",
      "type": "RSS",
      "status": "ACTIVE",
      "lastFetch": "1 min sedan",
      "itemsPerDay": 140
    }
  ],
  "total": 3
}
```

**Datakälla:**
- Scout `feeds.yaml` (om tillgänglig)

**Fallback:**
- Returnerar tom lista om feeds.yaml saknas

---

## Frontend Mapping

### Events

Backend → Frontend mapping:
- `event_id` → `id`
- `metadata.scout_source` → `source`
- `source_type` → `sourceType` (RSS/MANUAL)
- `metadata.scout_score` → `score` (0-100)
- `metadata.scout_detected_at` → `timestamp`
- `raw_payload` → `title` (first 100 chars), `summary` (first 200 chars)

### Sources

Backend → Frontend mapping:
- `feeds.yaml` feeds → `Source[]`
- `name` → `name`
- `url` → determines `type` (RSS/API/MAIL)
- `enabled` → `status` (ACTIVE/PAUSED)
- Scout events → `lastFetch`, `itemsPerDay`

---

## MVP Kontrakt

**Events:**
- ✅ `id` (string)
- ✅ `title` (string)
- ✅ `summary` (string)
- ✅ `source` (string)
- ✅ `sourceType` (RSS | MANUAL)
- ✅ `timestamp` (ISO string)
- ✅ `status` (INKOMMANDE | PÅGÅR | BEARBETAS | GRANSKNING | PUBLICERAD | ARKIVERAD)
- ✅ `score` (number, 0-100)
- ✅ `isDuplicate` (boolean)
- ⚠️ `content` (optional, only if available)
- ⚠️ `maskedContent` (optional, TODO)
- ⚠️ `draft` (optional, TODO)
- ⚠️ `citations` (optional, TODO)
- ⚠️ `privacyLogs` (optional, TODO)

**Sources:**
- ✅ `id` (string)
- ✅ `name` (string)
- ✅ `type` (RSS | API | MAIL)
- ✅ `status` (ACTIVE | PAUSED | ERROR)
- ✅ `lastFetch` (string, human-readable)
- ✅ `itemsPerDay` (number)

---

## TODO (Framtida)

1. **Events:**
   - Lägg till `maskedContent`, `draft`, `citations`, `privacyLogs` från privacy/drafting moduler
   - DB-persistens för events (för närvarande in-memory only)

2. **Sources:**
   - DB-persistens för sources (för närvarande feeds.yaml only)
   - Real-time status från scout service
   - Konfigurera sources via API (POST/PATCH/DELETE)

---

## Module Contract Compliance

### Allowed Core Imports ✅

Modulen använder endast tillåtna core-imports:
- `app.core.logging` (logger) - för privacy-safe logging
- `app.core.config` (settings) - via logging indirekt

### Inter-Module Dependencies ⚠️

Modulen har dependency på:
- `app.modules.privacy.privacy_service` - för att hämta events från in-memory store
  - Använder `_event_store` (privat variabel, bör refaktoreras till publik metod) och `get_event()` (publik metod)
  - Rationale: Events lagras i privacy-modulens in-memory store, console-modulen exponerar dem för frontend
  - TODO: Refaktorera `_event_store` till publik metod `list_events()` i privacy_service för bättre encapsulation

### Router Registration ✅

Registrerad i `app/main.py`:
```python
from app.modules.console.router import router as console_router
app.include_router(console_router, prefix="/api/v1", tags=["console"])
```

### Privacy-Safe Logging ✅

All logging följer privacy-policy:
```python
logger.info("events_list", extra={"limit": limit})
logger.error("events_list_failed", extra={"error_type": error_type})  # Never str(e)
```

- ✅ Inga payloads loggas
- ✅ Inga headers loggas  
- ✅ Inga paths loggas
- ✅ Endast `error_type`, aldrig `str(e)`

### Error Handling ✅

- Använder FastAPI `HTTPException` för fel
- Global exception handlers hanterar dem automatiskt
- DB-optional: Returnerar tom lista om DB/scout saknas (inte 500)

### Database ✅

- Inga egna DB-models
- DB-optional: Modulen fungerar utan DB (returnerar tom lista)

