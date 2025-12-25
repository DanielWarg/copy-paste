# Copy/Paste - Runtime Reality & Operational Details

**Syfte:** Detaljerad dokumentation av operativa verkligheten i prod_brutal och dev-lägen.  
**Målgrupp:** AI-assistenter, DevOps, och utvecklare som behöver förstå hur systemet faktiskt körs.

**Senast uppdaterad:** 2025-12-25

---

## ⚠️ Viktigt: Denna guide beskriver OPERATIVA verkligheten

**PROJECT_GUIDE.md** beskriver projektstruktur och arkitektur.  
**RUNTIME_REALITY.md** (denna fil) beskriver hur systemet faktiskt körs i olika profiler.

---

## Säkerhetsprofiler

Systemet körs i två huvudsakliga profiler:

### 1. Dev Profile (Development)

- **Backend:** Direkt HTTP-åtkomst på `http://localhost:8000`
- **Frontend:** Direkt HTTP-åtkomst till backend
- **Network:** Ingen proxy, ingen mTLS
- **Egress:** Tillåten (för utveckling och testning)
- **CORS:** Aktiverad (CORS_ORIGINS i config)

**Användning:** Lokal utveckling, testning, debugging

### 2. prod_brutal Profile (Production)

- **Backend:** Endast på `internal_net` (ingen extern åtkomst)
- **Frontend:** Via proxy (Caddy) på `https://localhost`
- **Network:** Proxy-first, mTLS enforcement
- **Egress:** **ZERO EGRESS** (blockerad på nätverksnivå + kodnivå)
- **CORS:** Irrelevant (mTLS ersätter CORS)

**Användning:** Production deployment, säkerhetskritiska miljöer

---

## Frontend ↔ Backend Kommunikation

### Dev Profile

```
Frontend (http://localhost:5173)
    │
    │ HTTP
    │
    ▼
Backend (http://localhost:8000)
```

**Konfiguration:**
- `VITE_API_BASE_URL=http://localhost:8000`
- Ingen proxy
- Ingen mTLS

### prod_brutal Profile

```
Frontend (http://localhost:5173)
    │
    │ HTTPS + mTLS
    │ (client cert required)
    │
    ▼
Proxy (Caddy) - https://localhost
    │
    │ HTTP (internal_net)
    │
    ▼
Backend (http://backend:8000)
    (internal_net only, not exposed)
```

**Konfiguration:**
- `VITE_API_BASE_URL=https://localhost`
- Alla API-anrop går via proxy
- Client-certifikat måste installeras i webbläsaren
- Se: `docs/MTLS_BROWSER_SETUP.md`

**⚠️ KRITISKT:** I prod_brutal kan frontend **INTE** prata direkt med `http://localhost:8000`.  
Backend är på `internal_net` och exponeras endast via proxy.

---

## Network Architecture

### Dev Profile

```yaml
# docker-compose.yml
services:
  backend:
    ports:
      - "8000:8000"  # Exposed externally
    networks:
      - app-network  # Standard bridge network
```

**Åtkomst:**
- Frontend → `http://localhost:8000` (direkt)
- Health check → `http://localhost:8000/health` (direkt)

### prod_brutal Profile

```yaml
# docker-compose.prod_brutal.yml
services:
  backend:
    ports: []  # NO external ports
    networks:
      - internal_net  # internal: true (no egress)
  
  proxy:
    ports:
      - "80:80"   # HTTP (health/ready only)
      - "443:443" # HTTPS (mTLS required)
    networks:
      - internal_net
```

**Åtkomst:**
- Frontend → `https://localhost` (via proxy, mTLS)
- Health check → `http://localhost/health` (HTTP, no mTLS)
- Backend → **INGEN direkt åtkomst** (endast via proxy)

---

## Record → Transcript Flow (Operativ Verklighet)

### API Flow

1. **Create Record:**
   ```
   POST /api/v1/record/create
   Body: { "title": "Audio upload" }
   Response: { "project_id": 1, "transcript_id": 1, ... }
   ```

2. **Upload Audio:**
   ```
   POST /api/v1/record/{transcript_id}/audio
   Content-Type: multipart/form-data
   Body: file=<audio file>
   Response: { "status": "uploaded", "file_id": 1, ... }
   ```

3. **Asynkron Processing:**
   - Backend processar audio i bakgrunden
   - Transcript status: `uploaded` → `transcribing` → `ready`

4. **UI Polling:**
   ```
   GET /api/v1/transcripts/{transcript_id}
   Response: { "id": 1, "status": "ready", "segments": [...] }
   ```
   - UI pollar var 2:e sekund
   - Max 60 försök (2 minuter timeout)

### Frontend Implementation

**Primary Implementation (REAL WIRED):**
- `frontend/views/RealRecorderPage.tsx` - Default startvy
- `frontend/core/api/realApiClient.ts` - API client (NO MOCK)
- `frontend/core/recorder/useRecorder.ts` - State management hook

**Flow:**
1. User väljer fil → `RealRecorderPage`
2. `recordApi.createRecord()` → Skapar record
3. `recordApi.uploadAudio()` → Upload audio
4. `useRecorder` hook → Pollar `transcriptApi.getTranscript()` var 2:e sekund
5. När status = "ready" → Visa transcript

**Legacy Implementation (finns kvar men inte default):**
- `frontend/components/AudioUpload.tsx` - Legacy component
- `frontend/apiClient.ts` - Legacy API client (kan ha mock fallbacks)

---

## Mock Mode Status

### Historik

Tidigare kunde frontend köra i "mock mode" med mock data.

### Nuvarande Status

- **Mock mode är INTE längre default**
- **Mock mode är legacy/dev-hjälpmedel**
- **Default är REAL WIRED** (ingen mock data)

**Vad som gäller:**
- `RealRecorderPage` är default startvy (REAL WIRED)
- `realApiClient.ts` har INGA mock fallbacks
- Legacy components (`AudioUpload`, `UniversalBox`) kan fortfarande ha mock, men används inte som default

**För AI-assistenter:**
- Anta att frontend är REAL WIRED som default
- Mock mode ska inte användas i prod eller verifieringsflöden
- Om du ser mock data i UI, det är ett problem (inte ett feature)

---

## Zero Egress (prod_brutal)

### Network Level

```yaml
networks:
  internal_net:
    internal: true  # No egress to internet
```

Backend kan **INTE** nå internet (Docker network isolation).

### Code Level

```python
# backend/app/core/config.py
def _validate_prod_brutal(self):
    if self.openai_api_key:
        raise ValueError("OPENAI_API_KEY forbidden in prod_brutal")
```

Backend **blockerar** cloud API keys i prod_brutal (fail-closed).

### Verifiering

```bash
# Runtime verification
make verify-brutal

# Verifierar:
# - Network isolation (no egress)
# - No cloud API keys
# - mTLS enforcement
```

---

## mTLS (Mutual TLS)

### Vad är mTLS?

Både klient och server autentiserar varandra med certifikat.

### I prod_brutal

- **Server certifikat:** Proxy (Caddy) har server certifikat
- **Client certifikat:** Webbläsare måste ha installerat client certifikat
- **Enforcement:** Alla HTTPS-requests kräver client certifikat

### Browser Setup

Se: `docs/MTLS_BROWSER_SETUP.md`

**Kort version:**
1. Exportera client certifikat (`.p12` eller `.pem`)
2. Installera i webbläsaren (Keychain på macOS, Certificate Manager på Windows)
3. Starta om webbläsaren
4. Navigera till `https://localhost`

### Error Handling

Om mTLS handshake misslyckas:
- Frontend visar tydligt felmeddelande
- Instruktioner: "Installera client certifikat. Se: docs/MTLS_BROWSER_SETUP.md"
- **INTE** en kryptisk stacktrace

---

## Health & Ready Endpoints

### Separation

**Health endpoints** är tillgängliga via HTTP (port 80) **utan** mTLS:
- `http://localhost/health` → 200 OK
- `http://localhost/ready` → 200 OK (om DB) eller 503 (om no DB)

**API endpoints** kräver HTTPS + mTLS:
- `https://localhost/api/v1/*` → 403 (utan cert) eller 200 (med cert)

### Rationale

- Monitoring tools behöver health checks (kan inte hantera mTLS)
- API-anrop kräver full säkerhet (mTLS)

---

## Port Mapping

### Dev Profile

| Service | External Port | Internal Port | Access |
|---------|---------------|---------------|---------|
| Backend | 8000 | 8000 | Direct HTTP |
| Frontend | 5173 | 5173 | Direct HTTP |
| PostgreSQL | 5432 | 5432 | Direct (optional) |

### prod_brutal Profile

| Service | External Port | Internal Port | Access |
|---------|---------------|---------------|---------|
| Proxy (HTTP) | 80 | 80 | Health/ready only |
| Proxy (HTTPS) | 443 | 443 | mTLS required |
| Backend | **NONE** | 8000 | Internal only |
| Frontend | **NONE** | - | Runs locally |
| PostgreSQL | **NONE** | 5432 | Internal only |

---

## Request Correlation

### Implementation

**Frontend:**
- `realApiClient.ts` genererar `X-Request-Id` per request (via interceptor)
- Alla API-anrop inkluderar `X-Request-Id` header

**Backend:**
- `RequestIDMiddleware` använder inkommande `X-Request-Id` om present
- Annars genererar ny `request_id`
- Returnerar `X-Request-Id` i response headers

**Logs:**
- Alla logs inkluderar `request_id` för traceability
- Brutal-safe: Inga payloads, bara `request_id` + error code

### Verification

```bash
# E2E test verifierar request correlation
make verify-ui-e2e

# Verifierar:
# - Frontend skickar X-Request-Id
# - Backend echoar samma request_id
# - Logs innehåller request_id
```

---

## Browser Testing Constraints

### mTLS i Playwright

Playwright kan hantera client certifikat, men kräver konfiguration:

```typescript
// playwright.config.ts
use: {
  contextOptions: {
    // Client certifikat för mTLS
    httpCredentials: {
      username: 'client',
      password: 'cert-password',
    },
  },
}
```

**Alternativ:** Använd separat test-profil (HTTP, no mTLS) för E2E-tester.

### Test Profile

För E2E-tester kan man använda:
- HTTP direkt till backend (dev profile)
- Eller mock mTLS i test-proxy

**Viktigt:** Test-profilen får **INTE** användas i prod_brutal.

---

## CORS vs mTLS

### Dev Profile

- **CORS:** Aktiverad (`CORS_ORIGINS` i config)
- **mTLS:** Ej aktiverad

### prod_brutal Profile

- **CORS:** Irrelevant (mTLS ersätter CORS)
- **mTLS:** Aktiverad (obligatoriskt)

**Rationale:** mTLS ger starkare säkerhet än CORS (client certifikat vs origin header).

---

## Sammanfattning för AI-assistenter

### När du arbetar med frontend ↔ backend integration:

1. **Dev:** Frontend → `http://localhost:8000` (direkt)
2. **prod_brutal:** Frontend → `https://localhost` (via proxy, mTLS)

### När du arbetar med Record/Transcript flow:

1. `POST /api/v1/record/create` → Skapar record
2. `POST /api/v1/record/{id}/audio` → Upload audio
3. Poll `GET /api/v1/transcripts/{id}` → Vänta på "ready"
4. UI visar transcript när klar

### När du arbetar med mock mode:

- **Mock mode är INTE default**
- **Mock mode är legacy**
- **Default är REAL WIRED**

### När du arbetar med säkerhet:

- **prod_brutal:** Zero egress, mTLS, fail-closed
- **dev:** Tillåtet för utveckling
- Se: `docs/security-complete.md` för detaljer

---

**Version:** 1.0.0  
**Senast uppdaterad:** 2025-12-25

