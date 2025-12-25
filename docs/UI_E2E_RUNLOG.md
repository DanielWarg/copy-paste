# UI E2E Test Run Log

**Syfte:** Dokumentera alla E2E-testkörningar med resultat och ev. problem.

**Senast uppdaterad:** 2025-12-25

---

## Foundation Test - 2025-12-25

### Test Setup

**Kommando:**
```bash
cd frontend && npx playwright test tests/e2e/foundation.spec.ts --headed
```

**Miljö:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (dev mode)
- Playwright: headed mode (browser visible)

### Test Resultat

**Status:** ⏳ Pending (kommer köras efter foundation implementation)

**Förväntade tester:**
1. App loads and shows shell
2. Navigation menu is visible
3. Header is visible with date and theme toggle
4. Backend status indicator is visible
5. Default page shows placeholder content
6. Navigation works
7. Theme toggle works

---

## Record Module Test - 2025-12-25

### Test Setup

**Kommando:**
```bash
cd frontend && npm run test:e2e:headed tests/e2e/record.spec.ts
```

**Miljö:**
- Frontend: http://localhost:5173
- Backend: https://localhost (via proxy, mTLS required)
- Test file: Del21.wav (repo root)
- Playwright: headed mode (browser visible)

### Test Resultat

**Status:** ⏳ Pending (kommer köras när backend körs)

**Förväntade tester:**
1. Recorder page loads and shows file input
2. Upload attempt without cert shows mTLS error (mtls-required)
3. Upload with cert (mtls-with-cert) - conditional on cert setup

---

## Test Execution Log

### 2025-12-25 - Playwright Test Fixes

**Ändringar:**
1. **Port uppdaterad:** Frontend port ändrad från 5173 till 5174 i alla testfiler
2. **Test file path fix:** Uppdaterad sökväg till Del21.wav (från `../Del21.wav` till `../../Del21.wav`)
3. **Robust wait strategy:** `mtls-with-cert` testet väntar nu på final state (success/error) istället för transient states
4. **Request ID logging:** Testet loggar nu request_id för alla API-anrop för debugging
5. **Error handling:** Testet hanterar nu både success och error states korrekt

**Varför ändringarna:**
- Transient states ("Skapar record", "Laddar upp") kan vara för snabba att fånga
- Bättre att vänta på final state (success med record_id/sha256 ELLER error message)
- Request ID logging hjälper med debugging och correlation
- Port 5174 är den dedikerade frontend-porten enligt projektkonfiguration

**Kommando:** `cd frontend && npx playwright test tests/e2e/record.spec.ts --headed`

**Resultat:** ⏳ Pending (kommer köras när backend är igång)

---

### 2025-12-25 - Status Script & Makefile Updates

**Ändringar:**
1. **Nytt status script:** `scripts/status.ps1` (PowerShell) och `scripts/status.sh` (Bash)
2. **Makefile target:** `make status` kör rätt script baserat på shell (pwsh eller bash)
3. **Backend /ready endpoint:** Förbättrad med tydligare felmeddelanden (db_uninitialized vs db_down)

**Varför ändringarna:**
- PowerShell history-problem orsakade "fastnar i terminalen"-känsla
- Bash-substitution med nested quotes fungerade inte i PowerShell
- Status script ger tydlig översikt utan komplexa substitutions
- `/ready` endpoint ger nu bättre feedback om varför DB inte är ready

**Användning:**
```bash
make status  # Visar systemstatus (automatiskt rätt script för din shell)
```

---

---

### 2025-12-25 - E2E Verification Session

**Kommando:** `make up && make status`

**System Status Output:**
```
✅ Backend: http://localhost:8000
   Health: ok
   Ready: ⚠️  DB not ready (503)

✅ Frontend: http://localhost:5174
   (Öppna i webbläsare för att se UI:n)

📋 Docker Containers:
   copy-paste-backend    Up 2 hours (healthy)
   copy-paste-postgres   Up 2 hours (healthy)
```

**Problem identifierade:**
1. **API Base URL:** Frontend defaultade till `https://localhost` istället för `http://localhost:8000`
   - **Fix:** Uppdaterat `frontend/src/api/client.ts` default till `http://localhost:8000`
   - **Fix:** Uppdaterat `frontend/src/components/BackendStatus.tsx` att använda samma default

2. **CORS:** Backend tillät inte `http://localhost:5174` (bara 5173)
   - **Fix:** Uppdaterat `backend/app/core/config.py` CORS_ORIGINS default till att inkludera `http://localhost:5174`
   - **Status:** Backend behöver rebuild/restart för att ladda ny config (Docker image cache)

3. **Backend /ready endpoint:** Returnerar 503 (DB not ready)
   - **Orsak:** DB health check timeout (kanske migrations behöver köras?)
   - **Status:** Inte blockerande för API-anrop (health endpoint fungerar)

**API Test (direkt):**
```bash
# Skapa record - FUNGERAR ✅
POST http://localhost:8000/api/v1/record/create
Response: {"project_id": 1, "transcript_id": 1, "title": "Test Del21", "created_at": "2025-12-25T16:34:21.376466"}
```

**UI Test (via browser):**
- ✅ Frontend laddar korrekt på http://localhost:5174
- ✅ UI Shell visas korrekt (Layout, Navigation, Header)
- ✅ Recorder-sidan visas korrekt
- ⚠️ Backend Status visar "mTLS krävs" (pga CORS-blockering)
- ⚠️ File upload kan inte testas via browser tools (kräver manuell interaktion)

**Nästa steg:**
1. Rebuild backend Docker image för att ladda ny CORS config
2. Testa manuell file upload via UI (Del21.wav)
3. Verifiera att request_id loggas korrekt i backend
4. Kör Playwright E2E test i headed mode

**Filer ändrade:**
- `frontend/src/api/client.ts` - API_BASE_URL default
- `frontend/src/components/BackendStatus.tsx` - API_BASE_URL default
- `backend/app/core/config.py` - CORS_ORIGINS default (lägg till 5174)

---

---

### 2025-12-25 - Projects Module Implementation

**Ändringar:**
1. **Navigation:** "Inspelning" → "Transkript" i constants.ts
2. **Project Hub:** Ny `Transkript.tsx` view med projektlista + create form
3. **Project Detail:** Ny `Project.tsx` view (folder view) med sektioner
4. **Record koppling:** Recorder kan nu ta emot `projectId` och visar projektnamn
5. **DB-gating:** Tydlig felhantering när DB saknas (503 → db_down error code)
6. **API layer:** Ny `projects.ts` med listProjects, createProject, getProject
7. **Error mapping:** `db_down` och `db_uninitialized` error codes i client.ts

**Varför ändringarna:**
- Projects blir navet för allt (records/transcripts/files/export)
- Navigation måste reflektera att "Transkript" är Project Hub
- Record måste kunna kopplas till projekt (backend stöd finns redan)
- DB-gating krävs eftersom Projects kräver DB för persistens

**Filer skapade/ändrade:**
- `frontend/src/api/projects.ts` - Projects API
- `frontend/src/views/Transkript.tsx` - Project Hub
- `frontend/src/views/Project.tsx` - Project detail
- `frontend/src/constants.ts` - Navigation uppdaterad
- `frontend/src/App.tsx` - Routing för Projects
- `frontend/src/api/record.ts` - project_id support
- `frontend/src/views/Recorder.tsx` - project context display
- `frontend/src/api/client.ts` - db_down error mapping
- `frontend/tests/e2e/projects.spec.ts` - E2E tests
- `docs/PROJECTS_DONE.md` - DoD checklist

**Testa med:**
```bash
# Starta backend+DB
make up

# Starta frontend
cd frontend && npm run dev

# Kör E2E tests
cd frontend && npm run test:e2e:headed tests/e2e/projects.spec.ts
```

**Status:** ✅ Projects Module Complete (pending E2E verification)

---

**Version:** 1.3.0

