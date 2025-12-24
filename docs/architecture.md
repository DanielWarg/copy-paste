# Systemarkitektur

**Senast uppdaterad:** 2025-12-24  
**Version:** 1.0.0

---

## Översikt

Copy/Paste är ett modulärt system för journalistisk AI-assistans med fokus på integritet, säkerhet och källskydd.

### Huvudkomponenter

```
┌─────────────────┐
│   Frontend      │  React + TypeScript (localhost:5173)
│   (UI)          │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│   Backend       │  FastAPI (localhost:8000)
│   (CORE)        │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
┌───▼───┐ ┌──▼──┐ ┌────▼────┐ ┌──▼─────┐
│Postgres│ │Scout│ │Privacy  │ │Modules │
│  (DB)  │ │(RSS)│ │Shield   │ │        │
└────────┘ └─────┘ └─────────┘ └────────┘
```

---

## Kommunikationsflöde

### 1. Frontend → Backend

**Protokoll:** HTTP/REST  
**Base URL:** `http://localhost:8000` (config via `VITE_API_BASE_URL`)

**Endpoints:**
- `/api/v1/transcripts` - Transcripts API
- `/api/v1/record/*` - Audio recording API
- `/api/v1/events` - Events API (Console module)
- `/api/v1/sources` - Sources API (Console module)
- `/api/v1/privacy/mask` - Privacy Shield API
- `/api/v1/projects/*` - Projects API
- `/health` - Health check
- `/ready` - Readiness check

**Error Handling:**
- Alla fel returnerar JSON med `error.code`, `error.message`, `error.request_id`
- Frontend fallback till mock-data om backend är offline

### 2. Backend → Database (PostgreSQL)

**Protokoll:** SQLAlchemy + Alembic  
**Connection:** `DATABASE_URL` env var  
**Features:**
- DB-optional (backend startar utan DB)
- Auto-migrations vid startup
- Connection pooling

**Tables:**
- `projects` - Projekt
- `transcripts` - Transkriptioner
- `transcript_segments` - Segment
- `audio_assets` - Audio-filer
- `service_state` - Service state

### 3. Backend → Scout (RSS Watcher)

**Protokoll:** Inter-process (Docker network)  
**Kommunikation:**
- Scout läser RSS feeds → skapar events
- Events lagras i `privacy_service._event_store` (in-memory)
- Backend läser events via Console module (`GET /api/v1/events`)

**Data Flow:**
```
RSS Feed → Scout → Event Store (in-memory) → Console Module → Frontend
```

**Notera:** Events lagras för närvarande in-memory. Framtida versioner kan använda persisterat event store.

### 4. Backend → Privacy Shield

**Protokoll:** Internal module calls  
**Användning:**
- Alla moduler kan anropa Privacy Shield för PII-maskning
- Hard gate för externa LLM-anrop (OpenAI, etc.)
- Defense-in-depth: regex → leak check → control check

**API:**
```python
from app.modules.privacy_shield.service import mask_text

masked = await mask_text(
    request=PrivacyMaskRequest(text="...", mode="strict"),
    request_id=request_id
)
```

### 5. External Egress (OpenAI, etc.)

**Protokoll:** HTTPS  
**Gate:** Privacy Shield (hard gate)  
**Policy:**
- Alla externa LLM-anrop MÅSTE gå via Privacy Shield
- Endast `MaskedPayload` accepteras (type-safe)
- Leak check preflight innan nätverkscall

**Flow:**
```
Raw Text → Privacy Shield → MaskedPayload → OpenAI Provider → External API
```

---

## Modularkitektur

### CORE (Frozen v1.0.0)

**Plats:** `backend/app/core/`  
**Ansvar:** Grundläggande infrastruktur  
**Komponenter:**
- `config.py` - Configuration (Pydantic Settings)
- `database.py` - DB connection & models
- `errors.py` - Global exception handlers
- `lifecycle.py` - Startup/shutdown hooks
- `logging.py` - Privacy-safe JSON logging
- `middleware.py` - Request ID, timing, security headers

**Principer:**
- Alltid startar (DB-optional)
- Privacy-by-default
- Security headers
- Modulär (ingen business logic)

### Aktiva Moduler

#### 1. Record Module
**Plats:** `backend/app/modules/record/`  
**Ansvar:** Audio recording, upload, export, destruction  
**Endpoints:**
- `POST /api/v1/record/` - Create record
- `POST /api/v1/record/{id}/upload` - Upload audio
- `GET /api/v1/record/{id}/export` - Export package
- `DELETE /api/v1/record/{id}` - Destroy record
- `GET /api/v1/record/{id}/export/{package_id}/download` - Download export

**Dokumentation:** `backend/app/modules/record/README.md`  
**Purge:** `backend/app/modules/record/purge.py` (CLI)

#### 2. Transcripts Module
**Plats:** `backend/app/modules/transcripts/`  
**Ansvar:** Transcript management  
**Endpoints:**
- `GET /api/v1/transcripts` - List transcripts
- `GET /api/v1/transcripts/{id}` - Get transcript
- `POST /api/v1/transcripts/{id}/export` - Export transcript

**Dokumentation:** `backend/app/modules/transcripts/README.md`

#### 3. Projects Module
**Plats:** `backend/app/modules/projects/`  
**Ansvar:** Project management  
**Endpoints:**
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project

**Dokumentation:** `backend/app/modules/projects/README.md` (saknas, behöver skapas)

#### 4. Console Module
**Plats:** `backend/app/modules/console/`  
**Ansvar:** Events och Sources endpoints för frontend  
**Endpoints:**
- `GET /api/v1/events` - List events
- `GET /api/v1/events/{id}` - Get event
- `GET /api/v1/sources` - List sources

**Dokumentation:** `backend/app/modules/console/README.md`

#### 5. Privacy Shield Module
**Plats:** `backend/app/modules/privacy_shield/`  
**Ansvar:** PII masking för externa LLM-egress  
**Endpoints:**
- `POST /api/v1/privacy/mask` - Mask PII in text

**Dokumentation:** `backend/app/modules/privacy_shield/README.md`  
**Status:** ✅ 100% test coverage (redteam test)

#### 6. Example Module
**Plats:** `backend/app/modules/example/`  
**Ansvar:** Reference implementation  
**Endpoints:**
- `GET /api/v1/example?q=test`

**Dokumentation:** `backend/app/modules/example/README.md`

### Moduler i Utveckling / Planerade

Inga moduler i aktiv utveckling för närvarande. Alla moduler i `backend/app/modules/` är aktiva och registrerade i `main.py`.

**Notera:** Äldre/experimentella moduler har arkiverats i `archive/modules/` för referens.

---

## Data Flow Exempel

### Audio Recording Flow

```
1. Frontend: POST /api/v1/record/ → Backend
2. Backend: Create record in DB → Return record_id
3. Frontend: POST /api/v1/record/{id}/upload → Backend (multipart/form-data)
4. Backend: 
   - Validate audio file
   - Encrypt file (Fernet)
   - Save to disk (/app/data/{sha256}.bin)
   - Update DB
5. Backend: Return file_id, sha256, size_bytes
6. Frontend: Display success
```

### Event Pipeline Flow

```
1. Console Module: Load events från Scout service (om tillgänglig) eller returnera tom lista
2. Frontend: GET /api/v1/events → Backend
3. Backend: Return events (från Scout om tillgänglig, annars tom lista)
4. Frontend: Display events in Console
```

**Notera:** Scout är en separat service (finns i `scout/` mapp) som inte är integrerad som backend-modul ännu. Console-modulen kan läsa events från Scout om den körs, annars returnerar den tom lista.

### Privacy Shield Flow

```
1. Module: Prepare text with PII (e.g., "Ring mig på 070-123 45 67")
2. Module: Call mask_text(request)
3. Privacy Shield:
   a. Baseline regex mask → "[PHONE]"
   b. Leak check → OK
   c. Control check (optional) → OK
4. Privacy Shield: Return MaskedPayload
5. Module: Use MaskedPayload for external LLM call
6. OpenAI Provider: Leak check preflight → OK
7. OpenAI Provider: API call → Response
```

---

## Säkerhetsarkitektur

### Defense in Depth

1. **Privacy Shield** - PII masking innan externa calls
2. **Security Headers** - X-Content-Type-Options, X-Frame-Options, etc.
3. **CORS** - Validerad, fail-fast om `*` i production
4. **Encryption** - File encryption (Fernet) för audio assets
5. **Privacy-Safe Logging** - Inga payloads/headers/PII i logs

### GDPR Compliance

1. **Data Minimization** - Purge module (automatisk rensning)
2. **Right to Erasure** - Destroy endpoints
3. **Privacy-by-Default** - Alla defaults är privacy-safe
4. **Retention Policies** - Configurable retention periods

---

## Deployment Architecture

### Lokal Utveckling

```
Frontend (localhost:5173) → Backend (localhost:8000) → PostgreSQL (localhost:5432)
                                                        Scout (Docker network)
```

### Docker Compose

```
docker-compose.yml:
  - postgres (port 5432)
  - backend (port 8000)
  - scout (internal)
```

**Volumes:**
- `./backend/data:/app/data` - Audio files, exports
- `./backend/data/dedupe.db` - Scout deduplication DB

---

## Ytterligare Dokumentation

- **CORE:** `docs/core.md` - Detaljerad CORE-dokumentation
- **Frontend:** `docs/frontend.md` - Frontend-arkitektur
- **Security:** `docs/security.md`, `docs/threat-model.md`
- **Moduler:** `backend/app/modules/*/README.md`

