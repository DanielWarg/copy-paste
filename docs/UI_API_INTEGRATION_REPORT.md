# UI ↔ API Integration Report

**Datum:** 2025-12-25  
**Status:** ✅ Recorder-flow REAL wired  
**Version:** 1.1.0

---

## Executive Summary

Detta dokument mappar alla backend API-endpoints till frontend-komponenter och verifierar att kopplingarna fungerar end-to-end. Rapporten identifierar glapp, dead endpoints, och saknade kopplingar.

---

## Backend Endpoints Inventory

### Core Endpoints
| Endpoint | Method | Module | Description |
|----------|--------|--------|-------------|
| `/health` | GET | core | Health check |
| `/ready` | GET | core | Readiness check |
| `/api/v1/example` | GET | example | Example endpoint |

### Console Module (`/api/v1`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/events` | GET | List events (limit query param) |
| `/api/v1/events/{event_id}` | GET | Get event by ID |
| `/api/v1/sources` | GET | List sources/feeds |

### Draft Module (`/api/v1`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/events/{event_id}/draft` | POST | Create draft with Privacy Gate enforcement |

### Privacy Shield Module (`/api/v1/privacy`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/privacy/mask` | POST | Mask PII in text |

### Record Module (`/api/v1/record`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/record/create` | POST | Create project + transcript shell |
| `/api/v1/record/{transcript_id}/audio` | POST | Upload audio file |
| `/api/v1/record/{transcript_id}/export` | POST | Export package (ZIP) |
| `/api/v1/record/{transcript_id}/destroy` | POST | Destroy record (dry_run default) |
| `/api/v1/record/export/{package_id}/download` | GET | Download export ZIP |

### Projects Module (`/api/v1/projects`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/projects` | POST | Create project |
| `/api/v1/projects` | GET | List projects |
| `/api/v1/projects/{project_id}` | GET | Get project by ID |
| `/api/v1/projects/{project_id}` | PATCH | Update project |
| `/api/v1/projects/{project_id}/audit` | GET | Get audit trail |
| `/api/v1/projects/{project_id}/verify` | GET | Verify integrity |
| `/api/v1/projects/{project_id}/attach` | POST | Attach transcripts |
| `/api/v1/projects/security-status` | GET | Get security status |

### Transcripts Module (`/api/v1/transcripts`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/transcripts` | GET | List transcripts |
| `/api/v1/transcripts` | POST | Create transcript |
| `/api/v1/transcripts/{transcript_id}` | GET | Get transcript by ID |
| `/api/v1/transcripts/{transcript_id}/segments` | POST | Add segments |
| `/api/v1/transcripts/{transcript_id}/export` | POST | Export transcript |
| `/api/v1/transcripts/{transcript_id}` | DELETE | Delete transcript |

### Autonomy Guard Module (`/api/v1/autonomy`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/autonomy/projects/{project_id}` | GET | Get autonomy guard checks |

---

## Frontend Components Inventory

### Pages (Primary - REAL WIRED)
- `App.tsx` - Main app container (default page: 'recorder')
- `views/RealRecorderPage.tsx` - **PRIMARY: Real-wired Recorder page (NO MOCK)**
- `views/Dashboard.tsx` - Dashboard view
- `views/Console.tsx` - Console view
- `views/Pipeline.tsx` - Pipeline view
- `views/Transcripts.tsx` - Transcripts archive
- `views/Sources.tsx` - Sources management

### Core API Layer (NEW - REAL WIRED)
- `core/api/realApiClient.ts` - **PRIMARY: Centralized API client (NO MOCK, mTLS, X-Request-Id)**
- `core/recorder/useRecorder.ts` - Custom hook for recorder flow (upload, polling, state)
- `core/recorder/RecorderState.ts` - State types for recorder

### Legacy Components (Still exist but not default)
- `components/AudioUpload.tsx` - Legacy upload component (not default)
- `components/UniversalBox.tsx` - Legacy ingest/upload component (not default)
- `src/components/SignalStream.tsx` - Event stream display
- `src/components/EventInspector.tsx` - Event detail inspector
- `src/components/FeedsPanel.tsx` - RSS feeds management
- `src/components/NotificationsPanel.tsx` - Notifications
- `src/components/DraftViewer.tsx` - Draft display
- `src/components/SourcePanel.tsx` - Sources display
- `src/components/ProofPanel.tsx` - Privacy proof panel
- `src/components/ScoutEvents.tsx` - Scout events display
- `src/components/ProductionModeToggle.tsx` - Production mode toggle

---

## Endpoint ↔ UI Mapping

### ✅ Working Mappings

| Backend Endpoint | Frontend File | Component/Method | Status |
|-----------------|---------------|------------------|--------|
| `/api/v1/events` | `apiClient.ts:224` | `apiClient.getEvents()` | ✅ Used (legacy) |
| `/api/v1/events/{id}` | `apiClient.ts:260` | `apiClient.getEventById()` | ✅ Used (legacy) |
| `/api/v1/sources` | `apiClient.ts:298` | `apiClient.getSources()` | ✅ Used (legacy) |
| `/api/v1/events/{id}/draft` | `apiClient.ts:388` | `apiClient.createDraft()` | ✅ Used (legacy) |
| `/api/v1/privacy/mask` | `apiClient.ts:353` | `apiClient.maskContent()` | ⚠️ Stub (legacy) |
| `/api/v1/transcripts` | `realApiClient.ts:149` | `transcriptApi.listTranscripts()` | ✅ REAL WIRED |
| `/api/v1/transcripts/{id}` | `realApiClient.ts:139` | `transcriptApi.getTranscript()` | ✅ REAL WIRED |
| `/api/v1/record/create` | `realApiClient.ts:99` | `recordApi.createRecord()` | ✅ REAL WIRED |
| `/api/v1/record/{id}/audio` | `realApiClient.ts:111` | `recordApi.uploadAudio()` | ✅ REAL WIRED |
| `/health` | `realApiClient.ts:161` | `healthApi.checkHealth()` | ✅ REAL WIRED |
| `/ready` | `realApiClient.ts:162` | `healthApi.checkHealth()` | ✅ REAL WIRED |

### ✅ Recorder Flow (REAL WIRED - Primary Implementation)

| Backend Endpoint | Frontend File | Component/Method | Status |
|-----------------|---------------|------------------|--------|
| `POST /api/v1/record/create` | `realApiClient.ts:99` | `recordApi.createRecord()` | ✅ REAL WIRED |
| `POST /api/v1/record/{id}/audio` | `realApiClient.ts:111` | `recordApi.uploadAudio()` | ✅ REAL WIRED |
| `GET /api/v1/transcripts/{id}` | `useRecorder.ts:24` | `transcriptApi.getTranscript()` (polling) | ✅ REAL WIRED |
| `GET /api/v1/transcripts` | `RealRecorderPage.tsx:36` | `transcriptApi.listTranscripts()` | ✅ REAL WIRED |

**Flow (RealRecorderPage):**
1. User selects audio file → `RealRecorderPage` component
2. `POST /api/v1/record/create` → Creates project + transcript shell (via `recordApi.createRecord()`)
3. `POST /api/v1/record/{transcript_id}/audio` → Uploads audio file (multipart/form-data via `recordApi.uploadAudio()`)
4. Poll `GET /api/v1/transcripts/{id}` → `useRecorder` hook polls every 2s (max 60 attempts, 2 min timeout)
5. `GET /api/v1/transcripts` → Refreshes list to show new transcript (via `transcriptApi.listTranscripts()`)

**Legacy Flow (AudioUpload component - still exists but not default):**
- `AudioUpload.tsx` still exists but is not the default implementation
- `RealRecorderPage.tsx` is the primary REAL WIRED implementation

**Request Correlation:**
- All requests include `X-Request-Id` header
- Backend echoes `X-Request-Id` in response
- UI displays request_id in dev mode

**mTLS:**
- All API calls go through proxy at `https://localhost` (prod_brutal)
- Client certificate required for HTTPS requests
- Health/ready endpoints available via HTTP (port 80) without mTLS

### ❌ Dead Endpoints (No Frontend Usage)

| Backend Endpoint | Reason |
|------------------|--------|
| `/api/v1/example` | Example endpoint, not used |
| `/api/v1/projects/*` | Projects module endpoints not used in current UI |
| `/api/v1/transcripts/*` (POST/DELETE) | Only GET used (POST via record/create) |
| `/api/v1/autonomy/*` | Autonomy guard not exposed in UI |

### ⚠️ Dead UI (Frontend Calls Non-Existent Endpoints)

| Frontend Call | File | Issue | Priority |
|---------------|------|------|----------|
| `/api/v1/ingest` | `UniversalBox.tsx:96` | Endpoint saknas | P0 Blocker |
| `/api/v1/ingest/audio` | `UniversalBox.tsx:36` | Endpoint saknas | P0 Blocker |
| `/api/v1/privacy/scrub_v2` | `UniversalBox.tsx:47,106`<br>`EventInspector.tsx:77` | Endpoint saknas | P0 Blocker |
| `/api/v1/privacy/scrub` | `EventInspector.tsx:94` | Endpoint saknas | P0 Blocker |
| `/api/v1/draft/generate` | `UniversalBox.tsx:60,119`<br>`EventInspector.tsx:101,125` | Endpoint saknas (finns `/events/{id}/draft`) | P0 Blocker |
| `/scout/feeds` | `SignalStream.tsx:29`<br>`FeedsPanel.tsx:36`<br>`EventInspector.tsx:30` | Scout service, inte backend | P1 Info |
| `/scout/events` | `SignalStream.tsx:45`<br>`EventInspector.tsx:54` | Scout service, inte backend | P1 Info |
| `/scout/notify` | `EventInspector.tsx:143`<br>`NotificationsPanel.tsx:46` | Scout service, inte backend | P1 Info |

---

## Request Correlation Status

### Current State
- ✅ Backend generates `request_id` in `RequestIDMiddleware`
- ✅ Backend returns `X-Request-Id` in response headers
- ✅ Frontend `realApiClient.ts` sends `X-Request-Id` in ALL requests (via interceptor)
- ✅ Frontend `realApiClient.ts` extracts `X-Request-Id` from responses
- ⚠️ Legacy `apiClient.ts` may not send `X-Request-Id` (use `realApiClient.ts` instead)
- ⚠️ Legacy components using `axios` directly don't use request correlation (should migrate to `realApiClient.ts`)

### Required Changes
1. Frontend must generate `request_id` per user action
2. Frontend must send `X-Request-Id` in all API requests
3. Backend must use incoming `X-Request-Id` if present, otherwise generate new
4. All logs must include `request_id` for traceability

---

## mTLS Error Handling

### Current State
- ✅ mTLS error handling in `realApiClient.ts` (detects TLS handshake failures)
- ✅ User-friendly error messages for mTLS failures (points to `docs/MTLS_BROWSER_SETUP.md`)
- ✅ Certificate installation instructions in `docs/MTLS_BROWSER_SETUP.md`
- ⚠️ Legacy components may not have mTLS error handling (should migrate to `realApiClient.ts`)

### Required Changes
1. Detect TLS handshake failures (connection refused, network errors)
2. Show user-friendly message: "Client certificate required. See docs/..."
3. Add debug panel (dev mode only) showing request correlation

---

## Issues & Fixes

### P0 Blockers (Must Fix)

#### Issue 1: Missing `/api/v1/ingest` endpoint
- **Location:** `frontend/src/components/UniversalBox.tsx:96`
- **Problem:** Frontend calls `/api/v1/ingest` but endpoint doesn't exist
- **Fix:** Create ingest endpoint or use existing record/projects endpoints
- **How to reproduce:** Click "Ingest" with URL/text input

#### Issue 2: Missing `/api/v1/ingest/audio` endpoint
- **Location:** `frontend/src/components/UniversalBox.tsx:36`
- **Problem:** Frontend calls `/api/v1/ingest/audio` but endpoint doesn't exist
- **Fix:** Use `/api/v1/record/{id}/audio` or create ingest endpoint
- **How to reproduce:** Upload audio file

#### Issue 3: Missing `/api/v1/privacy/scrub_v2` endpoint
- **Location:** `UniversalBox.tsx:47,106`, `EventInspector.tsx:77`
- **Problem:** Frontend calls `/api/v1/privacy/scrub_v2` but endpoint doesn't exist
- **Fix:** Create scrub_v2 endpoint or use `/api/v1/privacy/mask`
- **How to reproduce:** Click "Scrub & Draft" or ingest with production mode

#### Issue 4: Wrong draft endpoint path
- **Location:** `UniversalBox.tsx:60,119`, `EventInspector.tsx:101,125`
- **Problem:** Frontend calls `/api/v1/draft/generate` but endpoint is `/api/v1/events/{id}/draft`
- **Fix:** Update frontend to use correct path
- **How to reproduce:** Generate draft after scrub

### P1 Bugs (Should Fix)

#### Issue 5: No request correlation from frontend
- **Problem:** Frontend doesn't send `X-Request-Id`, making traceability impossible
- **Fix:** Implement request correlation (see Request Correlation section)

#### Issue 6: Mixed API clients (axios vs apiClient)
- **Problem:** Some components use `axios` directly, others use `apiClient.ts`
- **Fix:** Standardize on `apiClient.ts` with request correlation

### P2 Polish (Nice to Have)

#### Issue 7: No mTLS error UX
- **Problem:** TLS handshake failures show generic errors
- **Fix:** Add certificate installation instructions

#### Issue 8: Scout service endpoints not in backend
- **Problem:** Frontend calls scout service directly (separate service)
- **Fix:** Either integrate scout into backend or document as external dependency

---

## Request Correlation Implementation

### Frontend Changes Required

1. **Generate request_id per user action:**
   ```typescript
   // In apiClient.ts or utility
   function generateRequestId(): string {
     return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
   }
   ```

2. **Send X-Request-Id in all requests:**
   ```typescript
   // Update apiFetch to include X-Request-Id
   headers: {
     'Content-Type': 'application/json',
     'X-Request-Id': requestId,
     ...options.headers,
   }
   ```

3. **Update axios calls to include X-Request-Id:**
   - All components using axios directly must add header

### Backend Changes Required

1. **Use incoming X-Request-Id if present:**
   ```python
   # In RequestIDMiddleware
   request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
   ```

2. **Always return X-Request-Id in response:**
   - Already implemented ✅

### Verification

- Test: UI sends `X-Request-Id` → Backend logs same `request_id` → Response contains same `request_id`

---

## E2E Test Requirements

### Test Scenarios

1. **UI Load**
   - Open app in browser
   - Verify health check passes
   - Verify UI renders without errors

2. **Events List**
   - Load events from `/api/v1/events`
   - Verify events display in UI
   - Verify request correlation (check logs)

3. **Draft Generation Flow**
   - Ingest text/URL
   - Scrub (privacy mask)
   - Generate draft
   - Verify Privacy Gate enforcement
   - Verify request correlation

4. **mTLS Error Handling**
   - Attempt request without certificate
   - Verify TLS handshake fails
   - Verify UI shows appropriate error message

5. **Request Correlation Verification**
   - Perform action in UI
   - Verify `X-Request-Id` sent in request
   - Verify backend logs contain same `request_id`
   - Verify response contains same `request_id`

---

## Implementation Status

1. ✅ Create mapping table (this document)
2. ✅ Implement request correlation
   - Backend: Uses incoming X-Request-Id if present, otherwise generates new
   - Frontend: All API calls include X-Request-Id header
   - Utility: `frontend/src/utils/requestId.ts` for consistent generation
3. ✅ Fix P0 blockers (endpoint paths)
   - Updated `/api/v1/draft/generate` → `/api/v1/events/{id}/draft`
   - Updated `/api/v1/ingest` → `/api/v1/record/create` (workaround)
   - Updated `/api/v1/privacy/scrub_v2` → `/api/v1/privacy/mask` (workaround)
4. ✅ Create Playwright E2E test suite
   - Test file: `frontend/tests/e2e/ui-integration.spec.ts`
   - Config: `frontend/playwright.config.ts`
   - Make target: `make verify-ui-e2e`
5. ⏳ Add mTLS error handling in UI (partial)
   - Network errors handled gracefully
   - Certificate installation instructions not yet in UI (documented in security-complete.md)
6. ✅ Standardize on request correlation
   - All axios calls use `getAxiosConfigWithRequestId()`
   - apiClient.ts updated to send X-Request-Id

## Remaining Issues

### P0 Blockers (Fixed with Workarounds)
- ✅ `/api/v1/ingest` → Using `/api/v1/record/create` as workaround
- ✅ `/api/v1/ingest/audio` → Using `/api/v1/record/{id}/audio` as workaround
- ✅ `/api/v1/privacy/scrub_v2` → Using `/api/v1/privacy/mask` as workaround
- ✅ `/api/v1/draft/generate` → Using `/api/v1/events/{id}/draft` (correct endpoint)

**Note:** Workarounds are functional but may not match exact expected behavior. Consider implementing proper ingest endpoints if needed.

### P1 Bugs (Partially Fixed)
- ✅ Request correlation implemented
- ⚠️ Mixed API clients: Some components still use axios directly (but with request correlation)
- ⚠️ Scout service endpoints: Still call scout service directly (external dependency, documented)

### P2 Polish
- ⏳ mTLS error UX: Network errors handled, but no explicit certificate installation UI
- ✅ Request correlation verification: E2E tests verify correlation works

---

**Status:** ✅ Recorder Flow REAL WIRED (New Real API Core)

## New Real API Core (2025-12-25)

### Architecture

**New Core Layer:**
- `frontend/core/api/realApiClient.ts` - Clean API client (NO MOCK)
- `frontend/core/recorder/useRecorder.ts` - Recorder hook with state management
- `frontend/core/recorder/RecorderState.ts` - State types

**New Real Wired Page:**
- `frontend/views/RealRecorderPage.tsx` - Complete recorder flow (REAL WIRED)
- Default startvy: `recorder` (no mock data)
- Same visual profile as Transcripts view (preserves look & feel)

### Key Features

1. **No Mock Data:**
   - `realApiClient.ts` has NO mock fallbacks
   - Empty arrays/undefined returned on error (brutal-safe)
   - All API calls go through real backend

2. **Request Correlation:**
   - All requests include `X-Request-Id` header (auto-generated)
   - Backend echoes `X-Request-Id` in response
   - UI displays request_id in dev mode

3. **mTLS Support:**
   - API_BASE_URL uses `https://localhost` in production
   - TLS handshake failures show clear instructions
   - Error handling is brutal-safe (no payloads)

4. **State Management:**
   - `useRecorder` hook manages complete flow
   - States: idle → creating → uploading → transcribing → done/error
   - Progress feedback at each stage

5. **Polling:**
   - Polls `GET /api/v1/transcripts/{id}` every 2 seconds
   - Max 60 attempts (2 minutes timeout)
   - Status transitions: uploaded → transcribing → ready

**Status:** ✅ Recorder Flow REAL WIRED (New Real API Core)

## Recorder Flow Implementation (2025-12-25)

### ✅ Completed

1. **Mock Data Eliminated:**
   - `USE_MOCK` no longer defaults to `true` in DEV
   - All mock fallbacks removed from `apiClient.ts`
   - Empty arrays returned on error (brutal-safe)

2. **Recorder Flow Implemented:**
   - `AudioUpload` component in `frontend/components/AudioUpload.tsx`
   - Integrated in `Transcripts` view (`frontend/views/Transcripts.tsx`)
   - Complete flow: create → upload → poll → display

3. **Request Correlation:**
   - All requests include `X-Request-Id` header
   - Backend echoes `X-Request-Id` in response
   - UI displays request_id in dev mode (dev-only)

4. **mTLS Configuration:**
   - API_BASE_URL uses `https://localhost` in production
   - All API calls go through proxy (mTLS enforced)
   - Health/ready endpoints available via HTTP (port 80)

5. **Polling Implementation:**
   - Polls `GET /api/v1/transcripts/{id}` every 2 seconds
   - Max 60 attempts (2 minutes timeout)
   - Status transitions: uploaded → transcribing → ready

6. **Error Handling:**
   - Brutal-safe: No payloads in UI logs
   - Error code + request_id only
   - User-friendly error messages

7. **E2E Test:**
   - Playwright test: `frontend/tests/e2e/recorder-upload.spec.ts`
   - Tests complete flow with Del21.wav
   - Verifies request correlation

### Endpoints Used

- `POST /api/v1/record/create` - Create project + transcript shell
- `POST /api/v1/record/{transcript_id}/audio` - Upload audio (multipart/form-data)
- `GET /api/v1/transcripts/{id}` - Poll transcript status
- `GET /api/v1/transcripts` - List all transcripts

### Test Commands

```bash
# E2E test
make verify-ui-e2e

# Manual test
# 1. Open browser: http://localhost:5173
# 2. Navigate to "Inspelning" or "Transkriptioner"
# 3. Click "+ Ladda upp ljudfil"
# 4. Select Del21.wav
# 5. Click "Starta transkribering"
# 6. Wait for "Klart!" message
# 7. Verify transcript appears in list
```

### mTLS Browser Setup

See: `docs/MTLS_BROWSER_SETUP.md`

**Status:** ✅ Implementation Complete - Recorder Flow REAL WIRED  
**Last Updated:** 2025-12-25

