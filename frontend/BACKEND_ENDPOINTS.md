# Backend Endpoints - Översikt

## Implementerade Endpoints

### Transcripts
- ✅ `GET /api/v1/transcripts` - Lista transcripts (med filtering och search)
- ✅ `GET /api/v1/transcripts/{id}` - Hämta specifik transcript
- ✅ `POST /api/v1/transcripts` - Skapa transcript
- ✅ `POST /api/v1/transcripts/{id}/segments` - Lägg till/uppdatera segments
- ✅ `POST /api/v1/transcripts/{id}/export` - Exportera transcript (SRT/VTT/Quotes)
- ✅ `DELETE /api/v1/transcripts/{id}` - Ta bort transcript

### Record
- ✅ `POST /api/v1/record/create` - Skapa record (project + transcript)
- ✅ `POST /api/v1/record/{transcript_id}/audio` - Upload audio file
- ✅ `POST /api/v1/record/{transcript_id}/export` - Exportera package (ZIP)
- ✅ `POST /api/v1/record/{transcript_id}/destroy` - Förstöra record
- ✅ `GET /api/v1/record/export/{package_id}/download` - Hämta export ZIP

### Projects
- ✅ `GET /api/v1/projects` - Lista projects
- ✅ `GET /api/v1/projects/{id}` - Hämta specifik project
- ✅ `POST /api/v1/projects` - Skapa project
- ✅ `PATCH /api/v1/projects/{id}` - Uppdatera project
- ✅ `DELETE /api/v1/projects/{id}` - Ta bort project

### Health
- ✅ `GET /health` - Health check
- ✅ `GET /ready` - Readiness check

---

## Saknade Endpoints (för full frontend-kompatibilitet)

### 1. Events Endpoint (för Pipeline-vyn)
**Status:** ❌ Saknas

**Behövs:**
- `GET /api/v1/events` - Lista events (NewsEvent[])
- `GET /api/v1/events/{id}` - Hämta specifik event
- `POST /api/v1/events` - Skapa event

**Alternativ:**
- Använd scout-modulen om den exponerar events via API
- Eller bygg events-modul baserat på Transcripts/Projects

**UI Impact:**
- Pipeline-vyn använder mock data (`MOCK_EVENTS`)
- `apiClient.getEvents()` och `apiClient.getEventById()` fallback till mock

---

### 2. Sources Endpoint (för Sources-vyn)
**Status:** ❌ Saknas

**Behövs:**
- `GET /api/v1/sources` eller `GET /api/v1/scout/feeds` - Lista sources (Source[])
- `POST /api/v1/sources` - Lägg till source
- `PATCH /api/v1/sources/{id}` - Uppdatera source
- `DELETE /api/v1/sources/{id}` - Ta bort source

**Alternativ:**
- Använd scout-modulens `feeds.yaml` om den exponeras via API
- Eller bygg sources-modul baserat på RSS/API feeds

**UI Impact:**
- Sources-vyn använder mock data (`MOCK_SOURCES`)
- `apiClient.getSources()` fallback till mock

---

### 3. Privacy Shield Endpoint (för maskContent)
**Status:** ❌ Saknas

**Behövs:**
- `POST /api/v1/privacy/mask` - Maskera content
  - Request: `{ text: string }`
  - Response: `{ masked: string, logs: PrivacyLog[] }`

**Alternativ:**
- Använd autonomy_guard-modulen om den har maskeringsfunktionalitet

**UI Impact:**
- `apiClient.maskContent()` fallback till mock

---

### 4. Draft Generation Endpoint (för generateDraft)
**Status:** ❌ Saknas

**Behövs:**
- `POST /api/v1/events/{id}/draft` - Generera draft
  - Request: `{ event_id: string }`
  - Response: `{ draft: string, citations: Citation[] }`

**UI Impact:**
- `apiClient.generateDraft()` fallback till mock

---

## Frontend Adapter Status

### ✅ Implementerat
- Transcripts: `adaptTranscript()` mappar backend → UI format
- Error handling: `apiFetch()` hanterar JSON + non-JSON responses
- Request ID extraction: Från `X-Request-Id` header eller error body
- Export download: `downloadExport()` använder download endpoint

### ⚠️ Fallback till Mock
- Events: Använder `MOCK_EVENTS` (endpoint saknas)
- Sources: Använder `MOCK_SOURCES` (endpoint saknas)
- Privacy Shield: Använder mock (endpoint saknas)
- Draft Generation: Använder mock (endpoint saknas)

---

## Nästa Steg

1. **Events Endpoint:** Bygg events-modul eller exponera scout events
2. **Sources Endpoint:** Exponera scout feeds via API eller bygg sources-modul
3. **Privacy Shield:** Bygg privacy-modul med maskeringsfunktionalitet
4. **Draft Generation:** Bygg draft-modul eller integrera med AI-pipeline

