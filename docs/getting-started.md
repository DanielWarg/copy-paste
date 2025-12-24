# Getting Started - Copy/Paste System

**Senast uppdaterad:** 2025-12-24

---

## Snabbstart

### Förutsättningar

- Docker & Docker Compose installerat
- Node.js 18+ och npm (för frontend)
- Python 3.9+ (för lokala scripts, valfritt)

### Steg 1: Klona Repository

```bash
git clone <repository-url>
cd COPY:PASTE
```

### Steg 2: Konfigurera Environment

```bash
# Kopiera environment template (om .env saknas)
cp .env.example .env

# Redigera .env om behövs (defaults fungerar för lokal utveckling)
# Viktiga inställningar:
# - DATABASE_URL (default: postgresql://postgres:postgres@postgres:5432/copypaste)
# - RECORDER_RETENTION_DAYS (default: 14)
# - PRIVACY_MAX_CHARS (default: 50000)
```

### Steg 3: Starta Backend och Database

```bash
# Starta PostgreSQL + Backend i Docker
make up

# Verifiera att allt startade korrekt
make health
# Förväntat output:
# /health → 200 OK
# /ready → 200 OK (eller 503 om DB inte är klar)
```

**Vad händer:**
- PostgreSQL startar (port 5432)
- Backend startar (port 8000)
- Migrations körs automatiskt
- Backend är redo när `/ready` returnerar 200

### Steg 4: Starta Frontend

```bash
# I en separat terminal
make frontend-dev
```

**Vad händer:**
- Frontend startar på `http://localhost:5173`
- Ansluter till backend på `http://localhost:8000`
- UI öppnas automatiskt i webbläsaren

**Notera:** Frontend körs lokalt (inte i Docker) pga volymproblem med kolon i sökvägen (`COPY:PASTE`).

### Steg 5: Verifiera Installation

```bash
# Testa backend endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Testa att skapa ett projekt
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project","sensitivity":"standard"}'
```

---

## Vanliga Kommandon

### Docker Services

| Kommando | Vad det gör |
|----------|-------------|
| `make up` | Starta backend + postgres (Docker) |
| `make down` | Stoppa alla services |
| `make restart` | Starta om backend |
| `make logs` | Visa backend logs |
| `make health` | Testa health/ready endpoints |

### Testing

| Kommando | Vad det gör |
|----------|-------------|
| `make test` | Kör smoke tests |
| `make ci` | Quality checks (lint, format, typecheck) |
| `make verify` | GO/NO-GO verification |
| `make live-verify` | Live bulletproof test (real DB, no mocks) |

### Utveckling

| Kommando | Vad det gör |
|----------|-------------|
| `make frontend-dev` | Starta frontend dev server |
| `make migrate` | Kör migrations manuellt |
| `make shell` | Öppna Python shell i backend container |

---

## Projektstruktur

```
COPY:PASTE/
├── backend/                 # Backend (FastAPI)
│   ├── app/
│   │   ├── core/           # CORE foundation (frozen)
│   │   └── modules/        # Feature modules
│   │       ├── record/     # Audio recording
│   │       ├── transcripts/# Transcripts
│   │       ├── projects/   # Projects
│   │       ├── console/    # Events & Sources
│   │       └── privacy_shield/ # PII masking
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

### Backend Environment Variables

**Database:**
- `DATABASE_URL` - PostgreSQL connection string
- `DB_POOL_SIZE` - Connection pool size (default: 5)

**Security:**
- `SECRET_KEY` - Fernet encryption key (genereras automatiskt om saknas)
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)

**Privacy Shield:**
- `PRIVACY_MAX_CHARS` - Max input length (default: 50000)
- `PRIVACY_TIMEOUT_SECONDS` - Timeout for masking (default: 10)
- `ALLOW_EXTERNAL` - Allow external LLM calls (default: false)
- `OPENAI_API_KEY` - OpenAI API key (valfritt)

**Record Module:**
- `RECORDER_RETENTION_DAYS` - Retention period (default: 14)
- `RECORDER_PURGE_DRY_RUN` - Dry-run mode for purge (default: false)

**Logging:**
- `LOG_LEVEL` - Log level (default: INFO)
- `LOG_FORMAT` - Log format (json/text, default: json)

### Frontend Environment Variables

**API:**
- `VITE_API_BASE_URL` - Backend URL (default: http://localhost:8000)
- `VITE_USE_MOCK` - Use mock data (default: true)

---

## Nästa Steg

1. **Läs dokumentation:**
   - `docs/architecture.md` - Systemarkitektur
   - `docs/core.md` - CORE backend foundation
   - `docs/frontend.md` - Frontend arkitektur

2. **Utforska moduler:**
   - `backend/app/modules/*/README.md` - Module-specifik dokumentation

3. **Kör tester:**
   - `make test` - Smoke tests
   - `make live-verify` - Full system test

4. **Utveckla:**
   - Följ Module Contract (`docs/core.md`)
   - Skriv tests
   - Dokumentera i module README

---

## Troubleshooting

### Backend startar inte

```bash
# Kolla logs
make logs

# Kontrollera database connection
docker-compose exec backend python -c "from app.core.database import engine; engine.connect()"
```

### Frontend kan inte ansluta till backend

```bash
# Kontrollera att backend körs
curl http://localhost:8000/health

# Kontrollera CORS-inställningar
grep CORS_ORIGINS .env
```

### Migrations failar

```bash
# Kör migrations manuellt
make migrate

# Kontrollera database status
docker-compose exec postgres psql -U postgres -d copypaste -c "\dt"
```

### Port redan i bruk

```bash
# Ändra port i docker-compose.yml eller .env
# Eller stoppa annan service som använder porten
```

---

## Ytterligare Hjälp

- **README.md** - Huvuddokumentation och API docs
- **docs/** - Detaljerad dokumentation
- **CHANGELOG.md** - Versionshistorik

