# Copy/Paste - Journalistisk AI-Assistans

Modulärt system för journalistisk AI-assistans med fokus på integritet, säkerhet och källskydd.

---

## 📚 Dokumentationskarta

**Kom igång:**
- **[PROJECT_GUIDE.md](PROJECT_GUIDE.md)** ⭐ **START HÄR** - Komplett guide för projektstruktur, arkitektur och start
- **[Getting Started](docs/getting-started.md)** - Installationsguide och snabbstart
- **[Systemarkitektur](docs/architecture.md)** - Översikt över systemet och kommunikation
- **[README](README.md)** (denna fil) - Quick reference och API docs

**Huvuddokument:**
- **[CORE Backend](docs/core.md)** - CORE Backend Foundation (komplett teknisk dokumentation)
- **[Frontend](docs/frontend.md)** - Frontend arkitektur och implementation

**Security & Privacy:**
- **[Security](docs/security.md)** - Security measures, encryption, integrity checks
- **[Threat Model](docs/threat-model.md)** - Threat modeling och riskanalys
- **[OpSec](docs/opsec.md)** - Operational security, Docker hardening, egress control
- **[Journalism Safety](docs/journalism-safety.md)** - Source protection guidelines, retention policies
- **[User Safety](docs/user-safety.md)** - User safety guardrails, dry-run defaults
- **[Säkerhetsmoduler](docs/sakerhet-moduler.md)** - Översikt av säkerhetsmoduler

**Moduler:**
- **[Record Module](backend/app/modules/record/README.md)** - Audio recording, upload, export, destruction
- **[Transcripts Module](backend/app/modules/transcripts/README.md)** - Transcript management
- **[Projects Module](backend/app/modules/projects/README.md)** - Project management
- **[Autonomy Guard Module](backend/app/modules/autonomy_guard/README.md)** - Guardrails för autonoma handlingar
- **[Console Module](backend/app/modules/console/README.md)** - Events och Sources endpoints
- **[Privacy Shield Module](backend/app/modules/privacy_shield/README.md)** - PII masking för externa LLM-egress
- **[Example Module](backend/app/modules/example/README.md)** - Reference implementation

**Projektplanering:**
- **[CHANGELOG](CHANGELOG.md)** - Versionshistorik
- **[Agent Instructions](agent.md)** - Agent instructions (master prompt)

**Testing:**
- **[Test Results](tests/results/)** - Testresultat och rapporter
- **[Test Instructions](tests/instructions/)** - Testinstruktioner

---

## 🚀 Quick Start

### Snabbstart (3 kommandon)

```bash
# 1. Starta backend + database
make up

# 2. Starta frontend (i separat terminal)
make frontend-dev

# 3. Öppna webbläsaren
open http://localhost:5173
```

**Detaljerad guide:** Se [Getting Started](docs/getting-started.md)

---

## Systemöversikt

### Huvudkomponenter

- **Backend** (FastAPI) - `localhost:8000`
- **Frontend** (React + TypeScript) - `localhost:5173`
- **Database** (PostgreSQL) - `localhost:5432`
- **Scout** (RSS Watcher) - Docker network

**Detaljerad arkitektur:** Se [Systemarkitektur](docs/architecture.md)

---

## Vanliga Kommandon

### Docker Services

```bash
make up          # Starta backend + postgres
make down        # Stoppa alla services
make restart     # Starta om backend
make logs        # Visa backend logs
make health      # Testa health/ready endpoints
```

### Testing

```bash
make test            # Smoke tests
make ci              # Quality checks (lint, format, typecheck)
make verify          # GO/NO-GO verification
make live-verify     # Live bulletproof test (real DB, no mocks)
```

### Utveckling

```bash
make frontend-dev    # Starta frontend dev server
make migrate         # Kör migrations manuellt
make shell           # Öppna Python shell i backend container
```

**Alla kommandon:** Se [Getting Started](docs/getting-started.md)

---

## API Endpoints

### Core

- `GET /health` - Health check (alltid 200)
- `GET /ready` - Readiness check (200 om DB OK, 503 annars)

### Record Module

- `POST /api/v1/record/` - Create record
- `POST /api/v1/record/{id}/upload` - Upload audio file
- `GET /api/v1/record/{id}/export` - Export record package
- `DELETE /api/v1/record/{id}` - Destroy record
- `GET /api/v1/record/{id}/export/{package_id}/download` - Download export

**Dokumentation:** [Record Module](backend/app/modules/record/README.md)

### Transcripts Module

- `GET /api/v1/transcripts` - List transcripts
- `GET /api/v1/transcripts/{id}` - Get transcript
- `POST /api/v1/transcripts/{id}/export` - Export transcript

**Dokumentation:** [Transcripts Module](backend/app/modules/transcripts/README.md)

### Projects Module

- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project

### Console Module

- `GET /api/v1/events` - List events
- `GET /api/v1/events/{id}` - Get event
- `GET /api/v1/sources` - List sources

**Dokumentation:** [Console Module](backend/app/modules/console/README.md)

### Privacy Shield Module

- `POST /api/v1/privacy/mask` - Mask PII in text

**Dokumentation:** [Privacy Shield Module](backend/app/modules/privacy_shield/README.md)

**API Docs:** `http://localhost:8000/docs` (Swagger UI)

---

## Projektstruktur

```
COPY:PASTE/
├── backend/                 # Backend (FastAPI)
│   ├── app/
│   │   ├── core/           # CORE foundation (frozen v1.0.0)
│   │   └── modules/        # Feature modules
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # Frontend (React + TypeScript)
│   ├── src/               # Source code
│   └── package.json       # Node dependencies
├── scout/                 # RSS watcher service
├── docs/                  # Dokumentation
├── tests/                 # Test dokumentation & results
├── scripts/               # Test scripts
├── docker-compose.yml     # Docker services
└── Makefile              # Automation commands
```

---

## Konfiguration

### Environment Variables

**Backend (.env):**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Fernet encryption key
- `CORS_ORIGINS` - Allowed CORS origins
- `RECORDER_RETENTION_DAYS` - Retention period (default: 14)
- `PRIVACY_MAX_CHARS` - Max input length (default: 50000)
- `ALLOW_EXTERNAL` - Allow external LLM calls (default: false)

**Frontend (.env):**
- `VITE_API_BASE_URL` - Backend URL (default: http://localhost:8000)
- `VITE_USE_MOCK` - Use mock data (default: true)

**Fullständig lista:** Se [Getting Started](docs/getting-started.md)

---

## Säkerhet & Integritet

### Privacy-by-Default

- ✅ Inga payloads/headers/PII i logs
- ✅ Privacy Shield för externa LLM-anrop
- ✅ File encryption (Fernet) för audio assets
- ✅ GDPR-compliant retention (Purge module)

### Security Features

- ✅ Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- ✅ CORS validation (fail-fast om `*` i production)
- ✅ Defense-in-depth (Privacy Shield)
- ✅ Source protection (SOURCE_SAFETY_MODE)

**Detaljerad dokumentation:** Se [Security](docs/security.md) och [Threat Model](docs/threat-model.md)

---

## Development

### Module Contract

Alla moduler måste följa [Module Contract v1](docs/core.md#module-contract):

- ✅ Endast importera från `app.core.logging` och `app.core.config`
- ✅ Registrera router i `app/main.py`
- ✅ Privacy-safe logging (inga payloads/headers/PII)
- ✅ Dokumentation i `README.md`

**Reference implementation:** [Example Module](backend/app/modules/example/README.md)

### Testing

- **Unit tests:** `backend/app/modules/*/tests/`
- **Integration tests:** `scripts/test_*.py`
- **Live tests:** `make live-verify`

**Test results:** Se [tests/results/](tests/results/)

---

## Troubleshooting

### Backend startar inte

```bash
make logs              # Kolla logs
make health            # Testa health endpoint
docker-compose ps      # Kontrollera container status
```

### Frontend kan inte ansluta

```bash
curl http://localhost:8000/health  # Testa backend
grep VITE_API_BASE_URL .env        # Kontrollera config
```

### Migrations failar

```bash
make migrate           # Kör migrations manuellt
docker-compose exec postgres psql -U postgres -d copypaste -c "\dt"
```

**Mer hjälp:** Se [Getting Started](docs/getting-started.md#troubleshooting)

---

## Licens & Support

**Version:** 1.0.0  
**Status:** Production-ready (CORE frozen, moduler i utveckling)

**Dokumentation:** Se [Dokumentationskarta](#-dokumentationskarta) ovan.  
