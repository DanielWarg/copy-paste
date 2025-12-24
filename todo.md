# Copy/Paste v2 - TODO & Status

**Senast uppdaterad:** 2025-12-24  
**Status:** CORE v1 frozen, moduler i utveckling

---

## 📋 ÖVERSIKT

Detta dokument ger en komplett bild av vad som fungerar, vad som behöver fixas, och vad som ska byggas härnäst. Använd detta som referens om chatten startas om.

---

## ✅ VAD SOM FUNGERAR

### CORE Backend Foundation (FROZEN v1.0.0)

**Status:** ✅ Production-ready, frozen, inga ändringar utan ADR/PR

**Funktionalitet:**
- ✅ FastAPI app med modulär struktur
- ✅ Privacy-safe JSON logging (inga payloads/headers/PII)
- ✅ Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- ✅ Request ID middleware (X-Request-Id i alla responses)
- ✅ Global exception handling (konsekvent error-shape med request_id)
- ✅ DB-optional (app startar utan DB, `/ready` visar status)
- ✅ Health endpoints (`/health` alltid 200, `/ready` 200/503)
- ✅ CORS middleware (validerat, fail-fast om `*` i production)
- ✅ Config fail-fast (Pydantic Settings, validerar vid import)
- ✅ Alembic migrations (non-blocking startup)
- ✅ Docker + docker-compose setup
- ✅ Makefile med alla vanliga kommandon
- ✅ Quality gates (Ruff, mypy, pre-commit, CI)

**Dokumentation:**
- ✅ `core.md` - Komplett CORE-dokumentation
- ✅ `README.md` - Quick start, troubleshooting, API docs
- ✅ `CHANGELOG.md` - Versionshistorik

**Testning:**
- ✅ `make test` - Smoke tests (DB up, DB down, No-DB)
- ✅ `make ci` - Quality checks (lint, format, typecheck)
- ✅ `make verify` - GO/NO-GO verification
- ✅ `make live-verify` - Live bulletproof test (real DB, no mocks)

**Filer:**
- `backend/app/core/` - Alla core-moduler
- `backend/app/routers/` - Health, ready, meta
- `backend/app/main.py` - App wiring
- `docker-compose.yml` - Services setup
- `Makefile` - Automation

---

### Moduler (Implementerade)

#### 1. Example Module ✅

**Status:** ✅ Reference implementation, följer Module Contract v1

**Funktionalitet:**
- ✅ `GET /api/v1/example?q=test` - Simple endpoint
- ✅ Privacy-safe logging
- ✅ No core dependencies (endast `config` och `logging`)

**Filer:**
- `backend/app/modules/example/`

---

#### 2. Transcripts Module ✅

**Status:** ✅ Fungerar, DB-optional (memory fallback)

**Funktionalitet:**
- ✅ CRUD för transcripts
- ✅ Segment management (bulk upsert)
- ✅ Export (SRT, VTT, Quotes)
- ✅ Search/filter
- ✅ Memory store fallback (om DB saknas)
- ✅ Audit trail (no content)

**API Endpoints:**
- `POST /api/v1/transcripts` - Create transcript
- `GET /api/v1/transcripts` - List transcripts (search/filter)
- `GET /api/v1/transcripts/{id}` - Get transcript
- `POST /api/v1/transcripts/{id}/segments` - Upsert segments
- `POST /api/v1/transcripts/{id}/export` - Export (SRT/VTT/Quotes)
- `DELETE /api/v1/transcripts/{id}` - Delete transcript

**Filer:**
- `backend/app/modules/transcripts/`

**Testning:**
- ✅ `make test` inkluderar transcripts tests

---

#### 3. Projects Module ✅

**Status:** ✅ Fungerar, Project Thread Contract v1

**Funktionalitet:**
- ✅ CRUD för projects
- ✅ Integrity verification (`/verify` endpoint)
- ✅ Audit trail (no content)
- ✅ Attach transcripts to projects
- ✅ Project notes (CRUD)
- ✅ File upload (encrypted storage)
- ✅ Project files management

**API Endpoints:**
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project
- `PATCH /api/v1/projects/{id}` - Update project
- `GET /api/v1/projects/{id}/verify` - Verify integrity
- `GET /api/v1/projects/{id}/audit` - Get audit log
- `POST /api/v1/projects/{id}/attach` - Attach transcripts
- `POST /api/v1/projects/{id}/notes` - Create note
- `GET /api/v1/projects/{id}/notes` - List notes
- `POST /api/v1/projects/{id}/files` - Upload file

**Filer:**
- `backend/app/modules/projects/`

**Testning:**
- ✅ `make test` inkluderar projects tests

---

#### 4. Autonomy Guard Module ✅

**Status:** ✅ Fungerar, rule-based checks (no AI)

**Funktionalitet:**
- ✅ Rule-based security checks
- ✅ Project-level checks (unusually_short_transcript, low_confidence, etc.)
- ✅ System flags (audit events, no content)
- ✅ On-demand checks (`GET /api/v1/autonomy/projects/{id}`)

**API Endpoints:**
- `GET /api/v1/autonomy/projects/{project_id}` - Run checks

**Filer:**
- `backend/app/modules/autonomy_guard/`

---

#### 5. Record Module ⚠️

**Status:** ⚠️ Delvis fungerar, men har problem

**Funktionalitet:**
- ✅ Create record (project + transcript shell)
- ❌ Upload audio (500 error - behöver fixas)
- ✅ Export package (ZIP med transcript + audio + audit)
- ✅ Destroy record (dry_run default, confirm + receipt)

**Problem:**
1. ❌ **Upload 500 error** - `/api/v1/record/{id}/audio` returnerar 500
   - Rotorsak: Troligen DB-transaction eller encryption key issue
   - Status: Under debugging
2. ❌ **Module Contract violation** - Importerar från `app.core.database` och `app.core.privacy_guard`
   - Enligt `core.md` Module Contract: Moduler får endast importera `config` och `logging`
   - Status: Behöver fixas

**API Endpoints:**
- `POST /api/v1/record/create` - Create project + transcript ✅
- `POST /api/v1/record/{id}/audio` - Upload audio ❌ (500 error)
- `POST /api/v1/record/{id}/export` - Export package ✅
- `POST /api/v1/record/{id}/destroy` - Destroy record ✅

**Filer:**
- `backend/app/modules/record/`

**Testning:**
- ⚠️ `make live-verify` failar på upload-steg

---

### Security & Privacy

**Status:** ✅ Implementerat och verifierat

**Funktionalitet:**
- ✅ Privacy Guard (`app.core.privacy_guard`) - Förbjuder content/PII i logs/audit
- ✅ Source Safety Mode (`SOURCE_SAFETY_MODE`) - Hard mode i production
- ✅ Integrity checks (SHA256 hashes för transcripts, notes, files)
- ✅ Encrypted file storage (Fernet encryption, `PROJECT_FILES_KEY`)
- ✅ Audit trail (no content, only metadata)
- ✅ Retention policies (RETENTION_DAYS_DEFAULT, RETENTION_DAYS_SENSITIVE)
- ✅ Cleanup script (`scripts/cleanup_retention.py`)
- ✅ Docker hardening (non-root user, read-only filesystem, cap_drop: ALL)

**Dokumentation:**
- ✅ `docs/journalism-safety.md` - Source protection guidelines
- ✅ `docs/security.md` - Security measures
- ✅ `docs/opsec.md` - Operational security
- ✅ `docs/user-safety.md` - User safety guardrails
- ✅ `docs/threat-model.md` - Threat modeling

**Testning:**
- ✅ `make verify` inkluderar security checks
- ✅ `scripts/check_logs.py` - Verifierar log hygiene

---

### Frontend

**Status:** ✅ Grundläggande integration klar

**Funktionalitet:**
- ✅ React + TypeScript + Vite setup
- ✅ Connectivity check (optional, fail gracefully)
- ✅ Mock mode (om backend offline)
- ✅ API client (`apiClient.ts`)

**Problem:**
- ⚠️ Frontend körs lokalt (inte i Docker) pga volymproblem med kolon i sökvägen
- ⚠️ Ingen riktig integration med backend API ännu (endast connectivity check)

**Filer:**
- `frontend/`

**Testning:**
- ⚠️ Ingen automatiserad testning ännu

---

### Infrastructure

**Status:** ✅ Fungerar

**Funktionalitet:**
- ✅ Docker Compose (PostgreSQL + Backend)
- ✅ Alembic migrations (automatiska vid startup)
- ✅ Makefile (alla vanliga kommandon)
- ✅ CI/CD (GitHub Actions)
- ✅ Pre-commit hooks (Ruff, mypy)

**Filer:**
- `docker-compose.yml`
- `Makefile`
- `.github/workflows/ci.yml`
- `.pre-commit-config.yaml`

---

## ❌ VAD SOM BEHÖVER FIXAS

### 1. Record Module - Upload 500 Error 🔴 KRITISKT

**Problem:**
- `POST /api/v1/record/{id}/audio` returnerar 500 Internal Server Error
- `make live-verify` failar på upload-steg

**Rotorsaker (under investigation):**
- A) Encryption/Fernet key issue
- B) DB transaction problem
- C) File validation/IO issue
- D) Schema/serialization issue

**Steg för fix:**
1. ✅ Instrumentera säkert (safe debug logging)
2. ⏳ Pinpoint exakt var det failar (stacktrace)
3. ⏳ Klassificera 500 (A/B/C/D)
4. ⏳ Fixa minsta ändring som tar upload från 500 → 201
5. ⏳ Verifiera med `make live-verify-reset`

**Filer att fixa:**
- `backend/app/modules/record/router.py` (upload endpoint)
- `backend/app/modules/record/service.py` (upload_audio function)
- `backend/app/modules/projects/file_storage.py` (store_file, encrypt_content)

---

### 2. Record Module - Module Contract Violation ✅ LÖST

**Status:** ✅ **LÖST** - Module Contract har uppdaterats i `core.md`

**Lösning:**
- Module Contract i `core.md` har uppdaterats för att tillåta `app.core.database` och `app.core.privacy_guard`
- Dessa är nu definierade som stabila core-utilities som är del av det publika modul-kontraktet
- Record-modulen (och andra moduler) kan nu importera dessa utan att bryta Module Contract

**Uppdaterat Module Contract:**
- ✅ Tillåter `app.core.config` (Settings)
- ✅ Tillåter `app.core.logging` (logger)
- ✅ Tillåter `app.core.database` (Base, SessionLocal, get_db) - **NYTT**
- ✅ Tillåter `app.core.privacy_guard` (sanitize_for_logging, assert_no_content, compute_integrity_hash) - **NYTT**

**Filer uppdaterade:**
- ✅ `core.md` - Module Contract sektion uppdaterad

---

### 3. Frontend - Docker Volume Issue ⚠️

**Problem:**
- Frontend kan inte köras i Docker pga volymproblem med kolon i sökvägen
- Körs lokalt istället (`make frontend-dev`)

**Lösning:**
- Använd named volumes istället för bind mounts
- Eller fixa sökvägshantering i docker-compose.yml

**Prioritet:** Låg (fungerar lokalt)

---

## 🚀 VAD SOM SKA BYGGAS HÄRNÄST

### 1. Fixa Record Module Upload ⏳

**Prioritet:** 🔴 Hög (blockerar `make live-verify`)

**Steg:**
1. Fixa upload 500 error (se ovan)
2. ✅ Module Contract violation - LÖST (contract uppdaterat)
3. Verifiera med `make live-verify-reset` → `✅ LIVE GO`

**Efter fix:**
- Record-modulen är komplett och testad
- `make live-verify` passerar
- Systemet är redo för nästa modul

---

### 2. Frontend Integration "På Riktigt" ⏳

**Prioritet:** 🟡 Medium (efter Record fix)

**Funktionalitet:**
- Integrera frontend med backend API (inte bara connectivity check)
- Implementera UI för:
  - Projects (list, create, view)
  - Transcripts (list, view, export)
  - Record (create, upload, export, destroy)
- Real-time updates (om möjligt)

**Steg:**
1. Uppdatera `apiClient.ts` med riktiga API calls
2. Skapa UI-komponenter för varje modul
3. Testa end-to-end workflow
4. Dokumentera i `frontend.md`

---

### 3. Scout Module (RSS Feed Monitoring) ⏳

**Prioritet:** 🟡 Medium (efter Record fix)

**Funktionalitet:**
- RSS feed polling (intervallbaserad)
- Deduplicering (SQLite/PostgreSQL)
- Event scoring/prioritering
- Real-time notifieringar

**API Endpoints:**
- `GET /api/v1/scout/feeds` - List feeds
- `POST /api/v1/scout/feeds` - Add feed
- `PATCH /api/v1/scout/feeds/{id}` - Update feed
- `DELETE /api/v1/scout/feeds/{id}` - Delete feed
- `GET /api/v1/scout/events` - Get events
- `POST /api/v1/scout/feeds/{id}/poll` - Manual poll

**Steg:**
1. Skapa `backend/app/modules/scout/`
2. Implementera RSS polling
3. Implementera deduplication
4. Implementera event scoring
5. Testa med `make test`
6. Dokumentera i `backend/app/modules/scout/README.md`

---

### 4. Transcription Module (Audio → Text) ⏳

**Prioritet:** 🟡 Medium (efter Record fix)

**Funktionalitet:**
- Audio transcription (Faster-Whisper lokalt)
- Integration med Record module (transkribera uppladdad audio)
- Segment generation (speaker labels, timestamps, confidence)
- Lagring i Transcripts module

**API Endpoints:**
- `POST /api/v1/transcribe/audio` - Transcribe audio file
- `POST /api/v1/transcribe/{transcript_id}` - Transcribe existing record

**Steg:**
1. Skapa `backend/app/modules/transcribe/`
2. Integrera Faster-Whisper
3. Implementera transcription pipeline
4. Integrera med Record och Transcripts modules
5. Testa med real audio files
6. Dokumentera i `backend/app/modules/transcribe/README.md`

---

### 5. Privacy Shield Module (PII Anonymization) ⏳

**Prioritet:** 🟢 Låg (efter core modules)

**Funktionalitet:**
- Multi-layer anonymization (regex → LLM → verification)
- PII detection (email, phone, addresses, names, SSN, organizations)
- Token replacement (`[EMAIL_1]`, `[PERSON_A]`, etc.)
- Receipt system (spårbarhet)
- Approval workflow (human-in-the-loop)

**API Endpoints:**
- `POST /api/v1/privacy/scrub` - Anonymize text
- `GET /api/v1/privacy/receipt/{event_id}` - Get receipt
- `POST /api/v1/privacy/approve` - Approve gated event

**Steg:**
1. Skapa `backend/app/modules/privacy/`
2. Implementera regex fallback
3. Integrera Ollama (lokal LLM)
4. Implementera verification layer
5. Implementera receipt system
6. Testa med real data
7. Dokumentera i `backend/app/modules/privacy/README.md`

---

## 📝 NOTERINGAR

### Module Contract v1 ✅ UPPDATERAD

**Tillåtna imports från `app.core`:**
- ✅ `app.core.config` (Settings)
- ✅ `app.core.logging` (logger)
- ✅ `app.core.database` (Base, SessionLocal, get_db) - **Uppdaterat 2025-12-24**
- ✅ `app.core.privacy_guard` (sanitize_for_logging, assert_no_content, compute_integrity_hash) - **Uppdaterat 2025-12-24**

**Status:** Module Contract är uppdaterat i `core.md` (se [Module Contract](#module-contract) sektion). 
Record-modulen och andra moduler kan nu använda dessa imports utan att bryta contract.

**Förbjudet:** Direkta imports från andra `app.core` moduler utanför ovan lista (t.ex. middleware, lifecycle, errors är interna).

---

### Testning

**Nuvarande test-kommandon:**
- `make test` - Smoke tests (DB up, DB down, No-DB)
- `make ci` - Quality checks (lint, format, typecheck)
- `make verify` - GO/NO-GO verification
- `make live-verify` - Live bulletproof test (real DB, no mocks)
- `make live-verify-reset` - Live test med Docker reset

**Status:**
- ✅ CORE tests fungerar
- ✅ Module tests fungerar (transcripts, projects)
- ❌ Record tests failar (upload 500 error)

---

### Dokumentation

**Nuvarande dokumentation:**
- ✅ `README.md` - Quick start, API docs, troubleshooting
- ✅ `core.md` - Komplett CORE-dokumentation
- ✅ `ARBETSPLAN.md` - Projektplan (gammal, behöver uppdateras)
- ✅ `CHANGELOG.md` - Versionshistorik
- ✅ `frontend.md` - Frontend dokumentation
- ✅ `docs/` - Security, journalism-safety, opsec, etc.
- ✅ Module READMEs (i varje modul)

**Behöver uppdateras:**
- ⏳ `ARBETSPLAN.md` - Uppdatera med nuvarande status
- ✅ `core.md` - Module Contract uppdaterat 2025-12-24 (tillåter database och privacy_guard imports)

---

## 🎯 NÄSTA STEG (Prioriterat)

1. **🔴 Fixa Record Module Upload 500 Error**
   - Debug och pinpoint problem
   - Fixa minsta ändring
   - Verifiera med `make live-verify-reset`

2. **✅ Fixa Record Module Contract Violation** - LÖST
   - ✅ Module Contract uppdaterat i `core.md`
   - ✅ Tillåter nu `app.core.database` och `app.core.privacy_guard` imports

3. **🟡 Frontend Integration**
   - Implementera riktiga API calls
   - Skapa UI-komponenter
   - Testa end-to-end

4. **🟡 Scout Module**
   - Implementera RSS polling
   - Implementera deduplication
   - Testa och dokumentera

---

## 📚 REFERENSER

### Huvuddokument
- **`README.md`** - Quick start, API docs, troubleshooting, deployment
- **`core.md`** - CORE Backend Foundation (komplett teknisk dokumentation)
- **`frontend.md`** - Frontend arkitektur och implementation
- **`todo.md`** (denna fil) - Status, vad fungerar, vad behöver fixas, nästa steg

### Security & Privacy
- **`docs/journalism-safety.md`** - Source protection guidelines, retention policies
- **`docs/security.md`** - Security measures, encryption, integrity checks
- **`docs/opsec.md`** - Operational security, Docker hardening, egress control
- **`docs/threat-model.md`** - Threat modeling och riskanalys
- **`docs/user-safety.md`** - User safety guardrails, dry-run defaults
- **`docs/sakerhet-moduler.md`** - Översikt av säkerhetsmoduler

### Moduler
- **`backend/app/modules/*/README.md`** - Module-specifik dokumentation
  - `backend/app/modules/example/README.md` - Reference implementation
  - `backend/app/modules/transcripts/README.md` - Transcripts module
  - `backend/app/modules/projects/README.md` - Projects module
  - `backend/app/modules/record/README.md` - Record module (audio ingest)
  - `backend/app/modules/autonomy_guard/README.md` - Autonomy Guard module

### Projektplanering
- **`ARBETSPLAN.md`** - Projektplan (gammal, behöver uppdateras)
- **`CHANGELOG.md`** - Versionshistorik
- **`agent.md`** - Agent instructions template

### Snabbreferens
- **Quick Start:** `README.md` → [🚀 RUNBOOK - Quick Start](#-runbook---quick-start)
- **Module Contract:** `core.md` → [Module Contract](#module-contract)
- **API Endpoints:** `README.md` → [API Endpoints](#api-endpoints)

---

**Senast uppdaterad:** 2025-12-24  
**Nästa review:** Efter Record Module fix

