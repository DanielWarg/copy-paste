# Copy/Paste - Projektguide för AI-assistenter

**Syfte:** Komplett guide för att förstå projektstruktur, arkitektur, och hur systemet startas. Denna guide är designad för AI-assistenter som behöver få en fullständig bild av projektet.

**Senast uppdaterad:** 2025-12-24

---

## 📋 Innehållsförteckning

1. [Projektöversikt](#projektöversikt)
2. [Systemarkitektur](#systemarkitektur)
3. [Projektstruktur](#projektstruktur)
4. [Starta Systemet](#starta-systemet)
5. [Moduler & Komponenter](#moduler--komponenter)
6. [Teknisk Stack](#teknisk-stack)
7. [Viktiga Filer & Konfiguration](#viktiga-filer--konfiguration)
8. [Vanliga Kommandon](#vanliga-kommandon)
9. [Felsökning](#felsökning)

---

## Projektöversikt

**Copy/Paste** är ett modulärt system för journalistisk AI-assistans med fokus på integritet, säkerhet och källskydd.

### Kärnprinciper

- **Privacy-by-default:** Inga payloads, headers eller PII i logs
- **Modulär arkitektur:** Alla features i `/modules/*`, CORE är frozen
- **DB-optional:** App startar utan DB, `/ready` visar status
- **Fail-safe:** Security headers, error handling, observability
- **Source protection:** Integritet och säkerhet först

### Huvudfunktionalitet

- **Audio Recording:** Säker audio-ingest med kryptering
- **Transcripts:** Hantering och export av transkript
- **Projects:** Projektmanagement för journalister
- **Privacy Shield:** PII-masking för externa LLM-anrop
- **Console:** Events och Sources management
- **Autonomy Guard:** Guardrails för autonoma handlingar

---

## Systemarkitektur

### Översikt

```
┌─────────────┐
│  Frontend   │  React + TypeScript + Vite
│  (Port 5173)│  Mock mode eller Backend integration
└──────┬──────┘
       │ HTTP
       │
┌──────▼──────────────────────────────────────┐
│         Backend (FastAPI)                    │
│         Port 8000                            │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ CORE (Frozen v1.0.0)                 │  │
│  │ - Config, Logging, Middleware        │  │
│  │ - Database, Errors, Lifecycle        │  │
│  │ - Health, Ready endpoints            │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ MODULES (Active)                     │  │
│  │ - Record, Transcripts, Projects      │  │
│  │ - Privacy Shield, Console            │  │
│  │ - Autonomy Guard, Example            │  │
│  └──────────────────────────────────────┘  │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────┐
│ PostgreSQL  │  Port 5432 (optional)
│   (DB)      │  App fungerar utan DB
└─────────────┘
```

### Komponenter

1. **Frontend** (`frontend/`)
   - React + TypeScript
   - Kan köra i mock mode (utan backend)
   - Integrerar med backend via `VITE_API_BASE_URL`

2. **Backend** (`backend/`)
   - FastAPI application
   - Modulär struktur
   - CORE är frozen (ingen business logic)
   - Moduler i `backend/app/modules/`

3. **Database** (PostgreSQL)
   - Optional (app startar utan DB)
   - Alembic migrations
   - Health check via `/ready` endpoint

4. **Scout Service** (`scout/`)
   - Separat RSS-watcher service
   - Inte integrerad som backend-modul ännu
   - Console-modulen kan läsa events från Scout

---

## Projektstruktur

```
COPY:PASTE/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── core/              # CORE (frozen, no changes)
│   │   │   ├── config.py      # Settings (Pydantic)
│   │   │   ├── logging.py     # Privacy-safe JSON logging
│   │   │   ├── middleware.py  # Request ID, timing, headers
│   │   │   ├── database.py    # SQLAlchemy (optional)
│   │   │   ├── lifecycle.py   # Startup/shutdown hooks
│   │   │   ├── errors.py      # Global exception handlers
│   │   │   └── privacy_guard.py # Content/PII protection
│   │   ├── modules/           # Business logic modules
│   │   │   ├── example/       # Reference implementation
│   │   │   ├── transcripts/   # Transcript management
│   │   │   ├── projects/      # Project management
│   │   │   ├── record/        # Audio recording + purge
│   │   │   ├── console/       # Events & Sources
│   │   │   ├── privacy_shield/# PII masking
│   │   │   └── autonomy_guard/# Security guardrails
│   │   ├── routers/           # Core routers (health, ready, meta)
│   │   └── main.py            # FastAPI app wiring
│   ├── alembic/               # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React frontend
│   ├── src/                   # Source code
│   ├── views/                 # Page components
│   ├── components/            # Reusable components
│   ├── apiClient.ts           # API client (mock/real)
│   ├── Dockerfile
│   └── package.json
│
├── scout/                      # RSS watcher service (separat)
│   ├── rss_watcher.py
│   ├── dedupe_store.py
│   ├── scheduler.py
│   └── feeds.yaml
│
├── docs/                       # Dokumentation
│   ├── core.md                # CORE dokumentation
│   ├── frontend.md            # Frontend dokumentation
│   ├── architecture.md        # Systemarkitektur
│   ├── getting-started.md     # Startguide
│   └── security*.md           # Security docs
│
├── tests/                      # Testresultat & instruktioner
│   ├── results/               # Testrapporter
│   ├── instructions/          # Testinstruktioner
│   └── fixtures/              # Test data
│
├── scripts/                    # Utility scripts
│   ├── live_verify.py         # Live verification
│   ├── check_docs.sh          # Documentation validation
│   └── test_*.py              # Test scripts
│
├── docker-compose.yml          # Docker services
├── Makefile                   # Automation commands
├── README.md                  # Huvuddokumentation
├── CHANGELOG.md               # Versionshistorik
└── agent.md                   # Agent instructions (master prompt)
```

---

## Starta Systemet

### Snabbstart (3 kommandon)

```bash
# 1. Starta backend + database
make up

# 2. Starta frontend (i separat terminal)
make frontend-dev

# 3. Öppna browser
open http://localhost:5173
```

### Detaljerad Startguide

#### Förutsättningar

- Docker & Docker Compose installerat
- Node.js 18+ och npm (för frontend)
- Python 3.9+ (för scripts, valfritt)

#### Steg 1: Klona & Konfigurera

```bash
git clone <repository-url>
cd COPY:PASTE

# Kopiera .env om den saknas (defaults fungerar)
cp .env.example .env  # Om .env.example finns
```

#### Steg 2: Starta Backend + Database

```bash
# Starta PostgreSQL + Backend
make up

# Eller manuellt:
docker-compose up -d postgres backend

# Verifiera att backend kör
make health
# Förväntat: /health → 200, /ready → 200 (om DB) eller 503 (om no DB)
```

#### Steg 3: Starta Frontend

```bash
# Frontend körs lokalt (inte i Docker)
make frontend-dev

# Eller manuellt:
cd frontend
npm install
npm run dev
```

Frontend är tillgänglig på: `http://localhost:5173`

#### Steg 4: Verifiera

```bash
# Backend health
curl http://localhost:8000/health

# Backend ready (DB status)
curl http://localhost:8000/ready

# Frontend
open http://localhost:5173
```

---

## Moduler & Komponenter

### Aktiva Moduler (Registrerade i `main.py`)

#### 1. Example Module
**Endpoint:** `GET /api/v1/example?q=test`  
**Status:** ✅ Reference implementation  
**README:** `backend/app/modules/example/README.md`

#### 2. Transcripts Module
**Endpoints:** `GET/POST /api/v1/transcripts`, `POST /api/v1/transcripts/{id}/export`  
**Status:** ✅ Fungerar, DB-optional  
**README:** `backend/app/modules/transcripts/README.md`

#### 3. Projects Module
**Endpoints:** `GET/POST /api/v1/projects`, `GET /api/v1/projects/{id}/verify`  
**Status:** ✅ Fungerar  
**README:** `backend/app/modules/projects/README.md`

#### 4. Record Module
**Endpoints:** `POST /api/v1/record/create`, `POST /api/v1/record/{id}/audio`  
**Status:** ✅ Fungerar (inkl. purge CLI)  
**README:** `backend/app/modules/record/README.md`  
**Purge:** `backend/app/modules/record/purge.py` (CLI-baserad)

#### 5. Console Module
**Endpoints:** `GET /api/v1/events`, `GET /api/v1/sources`  
**Status:** ✅ Fungerar (kan läsa från Scout om tillgänglig)  
**README:** `backend/app/modules/console/README.md`

#### 6. Privacy Shield Module
**Endpoints:** `POST /api/v1/privacy/mask`  
**Status:** ✅ Fungerar, 100% test coverage  
**README:** `backend/app/modules/privacy_shield/README.md`

#### 7. Autonomy Guard Module
**Endpoints:** `GET /api/v1/autonomy/projects/{id}`  
**Status:** ✅ Fungerar  
**README:** `backend/app/modules/autonomy_guard/README.md`

---

## Teknisk Stack

### Backend
- **Framework:** FastAPI (Python 3.9+)
- **Database:** PostgreSQL (via SQLAlchemy, optional)
- **Migrations:** Alembic
- **Validation:** Pydantic
- **Logging:** Custom JSON logger (privacy-safe)
- **Testing:** pytest

### Frontend
- **Framework:** React 18+ (TypeScript)
- **Build Tool:** Vite
- **Styling:** Tailwind CSS (via CDN)
- **State:** React hooks
- **API Client:** Custom fetch wrapper (mock/real)

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Code Quality:** Ruff (linting), mypy (type checking)

---

## Viktiga Filer & Konfiguration

### Backend Konfiguration

**`backend/app/core/config.py`**
- Pydantic Settings
- Fail-fast validation
- Laddar från `.env` (repo root)

**Viktiga Environment Variables:**
```bash
# Database (optional)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/copypaste

# Security
PROJECT_FILES_KEY=<Fernet key, base64>
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Privacy Shield
LLAMACPP_BASE_URL=<optional>
ALLOW_EXTERNAL=false
OPENAI_API_KEY=<optional>
```

### Frontend Konfiguration

**`frontend/.env`**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=false  # true för mock mode
```

### Docker Compose

**`docker-compose.yml`**
- `postgres`: PostgreSQL database
- `backend`: FastAPI backend
- `frontend`: (Kommenterad ut, kör lokalt)

---

## Vanliga Kommandon

### Makefile Commands

```bash
# Services
make up              # Start backend + postgres
make down            # Stop all services
make restart         # Restart services
make logs            # Show logs

# Health & Testing
make health          # Check /health and /ready
make smoke           # Quick smoke test
make test            # Comprehensive smoke tests
make verify          # GO/NO-GO verification
make live-verify     # Live bulletproof test

# Code Quality
make lint            # Run ruff check
make format          # Run ruff format
make typecheck       # Run mypy
make ci              # lint + typecheck + test + check-docs

# Documentation
make check-docs      # Validate documentation

# Development
make frontend-dev    # Run frontend dev server
make purge           # Run record purge (GDPR retention)
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Execute commands
docker-compose exec backend python -m app.modules.record.purge_runner
```

---

## Felsökning

### Backend startar inte

```bash
# Kolla logs
make logs

# Kolla health
curl http://localhost:8000/health

# Starta om
make restart
```

### Database-problem

```bash
# Kolla DB status
docker-compose exec postgres psql -U postgres -d copypaste -c "\dt"

# Kör migrations manuellt
make migrate

# Eller:
docker-compose exec backend alembic upgrade head
```

### Frontend kan inte ansluta till backend

```bash
# Verifiera backend kör
curl http://localhost:8000/health

# Kontrollera VITE_API_BASE_URL i frontend/.env
# Standard: http://localhost:8000

# Frontend kan köra i mock mode (VITE_USE_MOCK=true)
```

### Port redan i bruk

```bash
# Ändra port i docker-compose.yml eller .env
# Backend: BACKEND_PORT=8001
# Frontend: FRONTEND_PORT=5174
```

---

## Ytterligare Resurser

### Viktig Dokumentation

- **`docs/core.md`** ⭐ **MÅSTE LÄSAS** - Komplett CORE backend dokumentation
  - **Module Contract** - Definierar hur nya moduler byggs (tillåtna/förbjudna imports)
  - Sektion: [Module Contract](docs/core.md#module-contract)
- **`README.md`** - Huvuddokumentation och API docs
- **`docs/frontend.md`** - Frontend arkitektur
- **`docs/architecture.md`** - Systemarkitektur och kommunikation
- **`docs/getting-started.md`** - Detaljerad startguide

### Module READMEs

Varje modul har egen README i `backend/app/modules/<module>/README.md`

### Security Docs

- `docs/security.md` - Security measures
- `docs/threat-model.md` - Threat modeling
- `docs/opsec.md` - Operational security
- `docs/journalism-safety.md` - Source protection
- `docs/user-safety.md` - User safety guardrails

---

## Module Contract - Bygga Nya Moduler

**⚠️ VIKTIGT:** Alla nya moduler MÅSTE följa Module Contract v1 definierat i `docs/core.md`.

**Komplett dokumentation:** Se **[docs/core.md - Module Contract sektion](docs/core.md#module-contract)** för fullständiga regler och exempel.

### Tillåtna Imports från `app.core`:

- ✅ `app.core.config` - Settings (Pydantic)
- ✅ `app.core.logging` - Structured logging
- ✅ `app.core.database` - Base, SessionLocal, get_db
- ✅ `app.core.privacy_guard` - sanitize_for_logging, assert_no_content, compute_integrity_hash

### Förbjudna Imports:

- ❌ `app.core.middleware` - Intern implementation
- ❌ `app.core.lifecycle` - Intern implementation
- ❌ `app.core.errors` - Intern implementation
- ❌ Direkta imports från andra core-moduler (endast de ovan)

### Krav på Nya Moduler:

1. **Struktur:**
   ```
   backend/app/modules/<name>/
   ├── __init__.py
   ├── router.py       # FastAPI router
   ├── service.py      # Business logic (valfritt)
   └── README.md       # Måste finnas!
   ```

2. **Router Registration:**
   - Registrera i `backend/app/main.py`
   - Använd prefix `/api/v1/<name>` eller `/api/v1`
   - Lägg till tags för Swagger

3. **Privacy-Safe Logging:**
   - Använd `logger.info("event_name", extra={...})` från `app.core.logging`
   - Aldrig logga payloads, headers, eller PII
   - Använd `sanitize_for_logging()` om osäker

4. **Dokumentation:**
   - Måste ha `README.md` i modulen
   - Dokumentera endpoints, data types, och funktionalitet
   - Se Example Module som referens

### Reference Implementation:

- **Example Module:** `backend/app/modules/example/` - Följer Module Contract perfekt
- **Module Contract Docs:** `docs/core.md` → [Module Contract](docs/core.md#module-contract)

**Innan du bygger en ny modul:** Läs Module Contract sektionen i `docs/core.md` noggrant!

---

## Snabbreferens för AI-assistenter

### Viktiga Principer

1. **CORE är frozen** - Inga ändringar i `backend/app/core/` utan ADR/PR
2. **Modulär design** - All business logic i `backend/app/modules/`
3. **Privacy-by-default** - Inga payloads/headers/PII i logs
4. **DB-optional** - App måste starta utan DB
5. **Module Contract** - Moduler får endast importera från `core.config`, `core.logging`, `core.database`, `core.privacy_guard`

### När du arbetar med projektet

1. **Läs `agent.md`** - Master prompt och arbetsinstruktioner
2. **Följ Module Contract** - Se `docs/core.md` → Module Contract sektion
3. **Testa lokalt** - Kör `make test` eller `make live-verify`
4. **Validera dokumentation** - Kör `make check-docs`
5. **Privacy-safe logging** - Använd structured logging, aldrig `str(e)` i prod

### Vanliga Arbetsflöden

**Lägga till ny modul:**
1. **Läs Module Contract** - Se `docs/core.md` → Module Contract sektion först!
2. Skapa `backend/app/modules/<name>/` struktur
3. Följ Module Contract strikt (tillåtna/förbjudna imports)
4. Skapa `README.md` i modulen (obligatoriskt)
5. Registrera router i `main.py`
6. Dokumentera endpoints och funktionalitet
7. Se Example Module som referens: `backend/app/modules/example/`

**⚠️ VIKTIGT:** Bryt aldrig Module Contract! Det är fundamentet för modulär arkitektur.

**Fixa bugg:**
1. Identifiera modul/komponent
2. Kolla module README för förståelse
3. Testa lokalt med `make test` eller `make live-verify`
4. Fixa minsta ändring som löser problemet
5. Verifiera med tester

---

**Version:** 1.0.0  
**Senast uppdaterad:** 2025-12-24

