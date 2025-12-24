# Projects Module

**Modul:** `app.modules.projects`

**Ansvar:** Projekt management - skapa och hantera projekt för journalister.

**Status:** ✅ Aktiv, registrerad i `main.py`

---

## Structure

```
backend/app/modules/projects/
├── __init__.py
├── models.py          # SQLAlchemy models (Project, ProjectNote, etc.)
├── router.py          # FastAPI router
├── file_storage.py    # File storage utilities
└── integrity.py       # Integrity verification
```

---

## Endpoints

### GET /api/v1/projects

Lista alla projekt.

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Project Name",
      "sensitivity": "standard",
      "created_at": "2025-12-24T10:00:00Z"
    }
  ],
  "total": 10
}
```

### POST /api/v1/projects

Skapa nytt projekt.

**Request:**
```json
{
  "name": "Project Name",
  "sensitivity": "standard" | "high" | "critical"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Project Name",
  "sensitivity": "standard",
  "created_at": "2025-12-24T10:00:00Z"
}
```

### GET /api/v1/projects/{id}

Hämta specifikt projekt.

**Response:**
```json
{
  "id": "uuid",
  "name": "Project Name",
  "sensitivity": "standard",
  "created_at": "2025-12-24T10:00:00Z",
  "notes": []
}
```

---

## Models

### Project

Huvudmodell för projekt.

**Fields:**
- `id` (UUID, primary key)
- `name` (string)
- `sensitivity` (enum: standard, high, critical)
- `created_at` (datetime)
- `notes` (relationship to ProjectNote)

### ProjectNote

Anteckningar kopplade till projekt.

**Fields:**
- `id` (UUID, primary key)
- `project_id` (UUID, foreign key)
- `note_body` (string, **förbjudet i logs**)
- `created_at` (datetime)

---

## File Storage

Modulen använder `file_storage.py` för filhantering. Se filen för detaljer.

---

## Integrity Verification

Modulen inkluderar integritetsverifiering via `integrity.py`. Se filen för detaljer.

---

## Module Contract Compliance

- ✅ **Core Imports:** Endast `app.core.logging` och `app.core.config`
- ✅ **Router Registration:** Registrerad i `app/main.py` med prefix `/api/v1/projects`
- ✅ **Privacy-Safe Logging:** Använder structured logging, ingen PII i logs
- ✅ **Database:** Använder SQLAlchemy models från `app.core.database`

---

## Testing

Modulen testas via:
- `scripts/test_projects_api.py`
- Integration tests i `make test`

