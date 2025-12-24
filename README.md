# Copy/Paste Core - Backend Foundation

Minimal, stable FastAPI backend foundation. Always starts, DB-optional, privacy-by-default logging, ready for modular growth.

## 🚀 RUNBOOK - Quick Start

**Första gången du startar systemet:**

### Steg 1: Förberedelser
```bash
# Klona/kör från projekt-root
cd /path/to/COPY:PASTE

# Kopiera environment template (om .env saknas)
cp .env.example .env
# Redigera .env om behövs (defaults fungerar för lokal utveckling)
```

### Steg 2: Starta Backend + Database
```bash
# Starta PostgreSQL + Backend i Docker
make up
```

**Vad händer:**
- PostgreSQL startar (port 5432)
- Backend startar (port 8000)
- Migrations körs automatiskt
- Backend är redo när du ser `{"status": "ready"}`

**Verifiera:**
```bash
make health
# Förväntat: /health → 200, /ready → 200
```

### Steg 3: Starta Frontend (lokalt)
```bash
# I en separat terminal
make frontend-dev
```

**Vad händer:**
- Frontend startar på `http://localhost:5173`
- Ansluter till backend på `http://localhost:8000`
- UI laddas i webbläsaren

**Notera:** Frontend körs lokalt (inte i Docker) pga volymproblem med kolon i sökvägen.

### Steg 4: Verifiera att allt fungerar
```bash
# Testa backend endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Testa att skapa ett projekt
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project","sensitivity":"standard"}'
```

### Vanliga Kommandon

| Kommando | Vad det gör |
|----------|-------------|
| `make up` | Starta backend + postgres (Docker) |
| `make down` | Stoppa alla services |
| `make logs` | Visa loggar från alla services |
| `make health` | Kolla `/health` och `/ready` |
| `make frontend-dev` | Starta frontend lokalt |
| `make test` | Kör smoke tests |
| `make live-verify` | Kör fullständig live-test (ingen mock) |

### Troubleshooting

**Backend startar inte:**
```bash
# Kolla loggar
make logs

# Kolla om port 8000 är upptagen
lsof -i :8000

# Starta om
make restart
```

**Database inte ansluten:**
```bash
# Kolla om postgres körs
docker ps | grep postgres

# Kolla backend loggar för db_init
docker logs copy-paste-backend | grep db_init

# Starta om
make restart
```

**Frontend kan inte ansluta till backend:**
```bash
# Verifiera backend körs
curl http://localhost:8000/health

# Kolla CORS i backend/.env
# Ska innehålla: CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Starta om backend efter CORS-ändring
make restart
```

---

## Architecture

CORE is a minimal backend that serves as the foundation for future modules. It provides:

- **Always starts**: No DB required, graceful degradation
- **Privacy-safe logging**: No payloads, no headers, no PII
- **Modular design**: Future features in `/modules/*`
- **Production-ready**: Docker, health checks, structured logging

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional, but recommended)

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (defaults work for local dev)
```

### 2. Start Services

**Rekommenderad setup (Docker backend + lokal frontend):**

```bash
# Terminal 1: Backend + Database
make up

# Terminal 2: Frontend (efter backend är igång)
make frontend-dev
```

**Vad som startar:**
- PostgreSQL (port 5432) - Docker
- Backend API (port 8000) - Docker
- Frontend (port 5173) - Lokalt (pga volymproblem med kolon i sökvägen)

**Alternativ: Allt lokalt (utan Docker):**
```bash
make dev
```

**Lifecycle Order (CRITICAL):**

När `make up` körs, startar services i denna exakta ordning:

1. **Config loaded** (fail-fast on errors)
2. **Logging initialized**
3. **Database initialized** (if `DATABASE_URL` exists)
4. **Migrations run** (if DB exists)
5. **Routers registered**
6. **App ready**

Detta säkerställer:
- Config errors fail fast (before logging)
- Logging available for DB init
- DB ready before `/ready` endpoint

### 3. Verify

```bash
make health
```

Expected output:
```json
{
  "status": "ok"
}
```

```json
{
  "status": "ready"
}
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make up` | Start backend + postgres (Docker) |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | Show logs from all services |
| `make health` | Check `/health` and `/ready` endpoints |
| `make frontend-dev` | Start frontend locally (port 5173) |
| `make dev` | Start backend + frontend locally (no Docker) |
| `make test` | Run smoke tests |
| `make live-verify` | Run full live test (no mock) |
| `make live-verify-reset` | Run live test with Docker reset |
| `make clean` | Stop services and remove volumes |

## API Endpoints

### `GET /health`

Always returns `200 OK` if process is alive.

**Response:**
```json
{
  "status": "ok"
}
```

### `GET /ready`

Readiness check endpoint. Behavior depends on `DATABASE_URL` configuration:

#### Scenario A: No DB configured (`DATABASE_URL` not set)

**Status:** `200 OK`

**Response:**
```json
{
  "status": "ready",
  "db": "not_configured"
}
```

#### Scenario B: DB configured and healthy (`DATABASE_URL` set, DB up)

**Status:** `200 OK`

**Response:**
```json
{
  "status": "ready"
}
```

#### Scenario C: DB configured but down (`DATABASE_URL` set, DB unreachable)

**Status:** `503 Service Unavailable`

**Response:**
```json
{
  "detail": {
    "status": "db_down",
    "message": "Database health check failed"
  }
}
```

**Timeout:** Health check respects `DB_HEALTH_TIMEOUT_SECONDS` (default 2.0s). Response returns within timeout period.

### Error Responses

All errors return a consistent JSON shape:

```json
{
  "error": {
    "code": "validation_error" | "http_error" | "internal_error",
    "message": "Human-readable error message",
    "request_id": "uuid-here"
  }
}
```

**Error Codes:**
- `validation_error` - Request validation failed (422)
- `http_error` - HTTP error (4xx, 5xx)
- `internal_error` - Unhandled exception (500)

**Debug Mode:**
- `DEBUG=false` (production): Generic messages, no stacktraces, no internal details
- `DEBUG=true` (development): More detailed error messages (still no headers/bodies/PII)

All error responses include `request_id` for traceability.

### `GET /meta` (Optional)

Only available when `ENABLE_META=true` in `.env`.

**Response:**
```json
{
  "version": "2.0.0",
  "build": "local",
  "commit": "unknown"
}
```

## Transcripts Module

The Transcripts module provides journalist-ready transcript management. See `backend/app/modules/transcripts/README.md` for full documentation.

**Endpoints:**
- `GET /api/v1/transcripts` - List/search transcripts
- `GET /api/v1/transcripts/{id}` - Get transcript with segments
- `POST /api/v1/transcripts` - Create transcript
- `POST /api/v1/transcripts/{id}/segments` - Upsert segments (replace all)
- `POST /api/v1/transcripts/{id}/export?format={srt|vtt|quotes}` - Export transcript
- `DELETE /api/v1/transcripts/{id}` - Delete transcript (hard delete)

### Projects Module

Project Thread Contract v1 - Central project management for all artifacts.

**Endpoints:**
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects (with counts)
- `GET /api/v1/projects/{id}` - Get project (with counts)
- `PATCH /api/v1/projects/{id}` - Update project (name, sensitivity, status)
- `GET /api/v1/projects/{id}/audit` - Get project audit events
- `GET /api/v1/projects/{id}/verify` - Verify project integrity
- `POST /api/v1/projects/{id}/attach` - Attach transcripts to project
- `GET /api/v1/projects/security-status` - Get security status

**Example:**
```bash
# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "sensitivity": "standard"}'

# List projects
curl http://localhost:8000/api/v1/projects

# Attach transcripts
curl -X POST http://localhost:8000/api/v1/projects/1/attach \
  -H "Content-Type: application/json" \
  -d '{"transcript_ids": [1, 2]}'

# Verify integrity
curl http://localhost:8000/api/v1/projects/1/verify
```

### Autonomy Guard Module

On-demand security checks (rule-based, NO AI).

**Endpoints:**
- `GET /api/v1/autonomy/projects/{project_id}` - Run autonomy checks for project

**Example:**
```bash
# Check project security
curl http://localhost:8000/api/v1/autonomy/projects/1?auto_flag=true
```

### Record Module

Secure audio ingest and management - get audio in 10 seconds.

**Endpoints:**
- `POST /api/v1/record/create` - Create project + transcript shell
- `POST /api/v1/record/{transcript_id}/audio` - Upload audio file (multipart/form-data)
- `POST /api/v1/record/{transcript_id}/export` - Export package (ZIP)
- `POST /api/v1/record/{transcript_id}/destroy` - Destroy record (dry_run default)

**Example:**
```bash
# Create record
curl -X POST http://localhost:8000/api/v1/record/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Recording", "sensitivity": "standard"}'

# Upload audio
curl -X POST http://localhost:8000/api/v1/record/1/audio \
  -F "file=@recording.wav"

# Export package
curl -X POST http://localhost:8000/api/v1/record/1/export \
  -H "Content-Type: application/json" \
  -d '{"confirm": true, "reason": "Export för granskning"}'

# Destroy (dry run first)
curl -X POST http://localhost:8000/api/v1/record/1/destroy \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
```

**Features:**
- Segmented transcripts with timestamps and speaker labels
- Search and filtering
- Export formats: SRT, VTT, Quotes
- DB-optional: Works with memory store if DB unavailable
- Privacy-safe: No transcript text in logs or audit metadata

## Lifecycle Order

**Note:** This section is duplicated in "Quick Start" above for visibility. See there for the critical startup sequence.

Startup sequence (CRITICAL):

1. **Config loaded** (fail-fast on errors)
2. **Logging initialized**
3. **Database initialized** (if `DATABASE_URL` exists)
4. **Migrations run** (if DB exists)
5. **Routers registered**
6. **App ready**

This order ensures:
- Config errors fail fast (before logging)
- Logging available for DB init
- DB ready before `/ready` endpoint

## Environment Variables

### Required

None - CORE can start without any configuration.

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `None` | PostgreSQL connection URL |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`) |
| `LOG_SAMPLE_RATE` | `1.0` | Log sampling rate (1.0 = log all, 0.1 = 10%) |
| `ENABLE_META` | `false` | Enable `/meta` endpoint |
| `DB_HEALTH_TIMEOUT_SECONDS` | `2.0` | DB health check timeout |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | CORS allowed origins (comma-separated, cannot be "*" in production) |
| `DEBUG` | `false` | Enable debug mode (more detailed errors, allows "*" in CORS) |
| `BACKEND_PORT` | `8000` | Backend port |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API base URL (set in `frontend/.env`) |
| `POSTGRES_USER` | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password |
| `POSTGRES_DB` | `copypaste` | PostgreSQL database name |

## Running Without Docker

### 1. Install Dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Setup Database (Optional)

If using PostgreSQL:

```bash
# Create database
createdb copypaste

# Set DATABASE_URL
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/copypaste

# Run migrations
cd backend
alembic upgrade head
```

### 3. Run Application

**Backend only:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend only:**
```bash
cd frontend
npm install
npm run dev
```

**Both (recommended):**
```bash
make dev
```

This starts both backend and frontend in parallel.

**Frontend Connection:**

- **Mock mode (default):** If `VITE_API_BASE_URL` is not set, frontend runs with mock data
- **CORE connection:** Set `VITE_API_BASE_URL` in `frontend/.env`:
  - **Local:** `VITE_API_BASE_URL=http://localhost:8000`
  - **Docker:** `VITE_API_BASE_URL=http://backend:8000` (set automatically in docker-compose)

Frontend performs optional connectivity checks against `/health` and `/ready`. If backend is unavailable, UI continues in mock mode (no crash).

## Troubleshooting

### Backend startar inte

**Symptom:** `make up` failar eller backend-containern kraschar.

**Kontrollera:**
```bash
# Kolla loggar
make logs
# eller
docker logs copy-paste-backend

# Kolla om port 8000 är upptagen
lsof -i :8000

# Starta om
make restart
```

**Vanliga orsaker:**
- Port 8000 redan används → Stoppa annan process eller ändra `BACKEND_PORT` i `.env`
- Database connection failar → Kolla `DATABASE_URL` i `.env` och att postgres körs
- Config error → Kolla loggar för exakt felmeddelande

### Database inte ansluten

**Symptom:** `/ready` returnerar 503 eller `db_init_failed` i loggar.

**Kontrollera:**
```bash
# Kolla om postgres körs
docker ps | grep postgres

# Kolla backend loggar
docker logs copy-paste-backend | grep -E "(db_init|migration|error)"

# Testa database connection
docker exec copy-paste-postgres psql -U postgres -d copypaste -c "SELECT 1"
```

**Fix:**
```bash
# Starta om allt
make restart

# Om migrations failar, kör manuellt
docker exec copy-paste-backend python3 -m alembic upgrade head
```

### CORS Errors

**Symptom:** Browser console shows CORS errors when frontend tries to connect to backend.

**Fix:**
1. Check `.env` file (root) contains `CORS_ORIGINS` with frontend URL:
   ```
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```
2. Format: Comma-separated list, no spaces around commas
3. Restart backend after changing `.env`:
   ```bash
   make restart
   ```

### Frontend kan inte ansluta till backend

**Symptom:** Frontend shows "backend offline" or continues in mock mode.

**Kontrollera:**
```bash
# Verifiera backend körs
curl http://localhost:8000/health

# Kolla frontend/.env
cat frontend/.env
# Ska innehålla: VITE_API_BASE_URL=http://localhost:8000

# Starta om frontend efter .env-ändring
# (stoppa med Ctrl+C och kör make frontend-dev igen)
```

**Expected behavior:** Frontend gracefully falls back to mock mode if backend is unavailable. UI should never crash.

### Frontend volymproblem i Docker

**Symptom:** `docker-compose up` failar med "invalid volume specification" för frontend.

**Orsak:** Kolon i sökvägen (`COPY:PASTE`) orsakar problem med Docker volume mounts.

**Lösning:** Kör frontend lokalt istället:
```bash
make frontend-dev
```

Detta är den rekommenderade setupen just nu.
3. Refresh frontend

## Development

### Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── logging.py       # Structured logging
│   │   ├── middleware.py    # Request ID, timing
│   │   ├── database.py      # SQLAlchemy setup
│   │   └── lifecycle.py     # Startup/shutdown
│   ├── routers/
│   │   ├── health.py        # /health endpoint
│   │   ├── ready.py         # /ready endpoint
│   │   └── meta.py          # /meta endpoint
│   └── modules/             # Future feature modules
├── alembic/                 # Database migrations
└── requirements.txt
```

### Adding a Module

See `core.md` for Module Contract v1.

## Example Module

A reference implementation demonstrating **Module Contract v1** is available at `backend/app/modules/example/`.

### Purpose

The example module serves as:
- **Template**: Shows how to structure modules according to Module Contract v1
- **Proof of concept**: Demonstrates that the module system works
- **Reference**: Documents the contract requirements

### Endpoint

**`GET /api/v1/example`**

Returns a simple status response.

**Response:**
```json
{
  "status": "ok",
  "module": "example"
}
```

### Module Contract Compliance

- ✅ No core dependencies (only `app.core.logging`)
- ✅ Privacy-safe logging (no headers, no body, no PII)
- ✅ Router registration in `app/main.py`
- ✅ No database requirements
- ✅ Simple error handling

See `backend/app/modules/example/README.md` for full documentation.

## CI/CD

### GitHub Actions

Continuous Integration runs on every push and pull request via `.github/workflows/ci.yml`.

**CI Pipeline:**
1. Checkout code
2. Set up Python 3.11
3. Install dependencies (`backend/requirements.txt` + `backend/requirements-dev.txt`)
4. Run quality checks:
   - `ruff check` (linting)
   - `ruff format --check` (format check)
   - `mypy` (type checking)
5. Verify Python syntax (`python -m compileall`)
6. Run core tests (`make test`)

All checks must pass for CI to succeed.

### Pre-commit Hooks

Pre-commit hooks run quality checks automatically before each commit.

**Setup:**
```bash
# Install pre-commit
pip install -r backend/requirements-dev.txt

# Install hooks
pre-commit install
```

**Manual run:**
```bash
pre-commit run --all-files
```

**Quality checks:**
- `ruff check` - Linting
- `ruff format` - Code formatting
- `mypy` - Type checking

### Local Quality Checks

```bash
make lint      # Run ruff check
make format    # Run ruff format
make typecheck # Run mypy type check
make ci        # Run all checks + tests
make smoke     # Manual smoke tests (curl endpoints)
```

### Log Privacy Check

Verify that logs don't contain forbidden keys (authorization, cookie, body, headers, etc.):

```bash
# Check Docker logs
python3 scripts/check_logs.py

# Or manually check
docker logs copy-paste-backend | grep -iE '(authorization|cookie|body|headers)' || echo "No violations found"
```

```bash
make lint      # Run ruff check
make format    # Run ruff format
make typecheck # Run mypy type check
make ci        # Run all checks + tests
```

## Testing

### Smoke Tests

```bash
make test
```

This runs three test scenarios:

**Scenario A: No DB configured**
- Starts backend without `DATABASE_URL`
- Verifies `/health` returns 200
- Verifies `/ready` returns 200 with `{"status": "ready", "db": "not_configured"}`

**Scenario B: DB up**
- Starts full stack (PostgreSQL + Backend)
- Verifies `/health` returns 200
- Verifies `/ready` returns 200 with `{"status": "ready"}`
- Verifies `/api/v1/example` returns 200 with `{"status": "ok", "module": "example"}`
- Verifies `/api/v1/example` returns 200 with `{"status": "ok", "module": "example"}`

**Scenario C: DB down**
- Stops PostgreSQL but keeps backend running
- Verifies `/ready` returns 503 within timeout (< 4 seconds)
- Verifies response contains `{"detail": {"status": "db_down"}}`

### Manual Testing

```bash
# Start services
make up

# Check health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/ready

# Check meta (if enabled)
curl http://localhost:8000/meta
```

## Privacy & Security

- **Privacy-safe logging**: No request/response bodies, no headers, no PII
- **Request ID**: Every request gets unique `X-Request-Id` header
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
- **Fail-fast config**: Invalid configuration stops boot immediately
- **No secrets in code**: All secrets via environment variables

## Additional Troubleshooting

**Notera:** Se RUNBOOK-sektionen ovan för grundläggande troubleshooting.

### `/meta` returns 404

This is expected if `ENABLE_META=false` (default). Set `ENABLE_META=true` in `.env` to enable.

## Deployment

### Docker Compose

```bash
make up
```

### Production Considerations

1. Set `ENABLE_META=false` (default)
2. Set `LOG_SAMPLE_RATE=0.1` for high traffic
3. Use strong `POSTGRES_PASSWORD`
4. Configure `CORS_ORIGINS` for your frontend domain
5. Set `LOG_LEVEL=WARNING` in production

## License

MIT

## CORE v1 Freeze

**CORE v1.0.0** is frozen and should not be modified without an ADR (Architecture Decision Record) or PR review.

**Policy:**
- All new functionality must go into `/modules/*`
- CORE changes require explicit approval
- CORE is considered stable and production-ready

**Release Tag:**
```bash
git tag -a core-v1.0.0 -m "CORE v1.0.0 - Stable foundation"
git push origin core-v1.0.0
```

## CORE v1 Freeze

**CORE v1.0.0** is frozen and should not be modified without an ADR (Architecture Decision Record) or PR review.

**Policy:**
- All new functionality must go into `/modules/*`
- CORE changes require explicit approval
- CORE is considered stable and production-ready

**Release Tag:**
```bash
git tag -a core-v1.0.0 -m "CORE v1.0.0 - Stable foundation"
git push origin core-v1.0.0
```

## Live Bulletproof Test

**Purpose:** End-to-end verification with real Docker DB + backend + audio fixtures (NO MOCK).

**Commands:**
```bash
# Standard test (services must be running)
make live-verify

# Test with Docker reset (docker compose down -v before test)
make live-verify-reset
```

**What it tests:**
- A) (Optional) Reset: `docker compose down -v` if `--reset` flag used
- B) Service health: Backend up, `/health`, `/ready`
- C) Health/Ready + security headers: Verifies `Cache-Control=no-store`, `Referrer-Policy`, `Permissions-Policy`, `X-Content-Type-Options`
- D) Projects live: Create standard/sensitive (name contains run_id), list, get, patch, verify integrity
- E) Record live: Create, upload audio (wav/mp3), export encrypted, verify manifest (no forbidden keys), verify audio encrypted (no WAV header), destroy dry_run, destroy confirm, destroy repeat (idempotent)
- F) Transcripts live: Create (title contains run_id), segments replace-all (3-5), export SRT (verify `00:00:00,000` format), attach to project
- G) Autonomy Guard: Run checks, verify audit events created (no content/identifiers)
- H) Log hygiene + audit hygiene: Run `check_logs.py`, verify audit tables (no forbidden keys)
- I) Production simulation: Test boot failure with `DEBUG=false` and `SOURCE_SAFETY_MODE=false`, test correct boot with `DEBUG=false`
- J) Cleanup: Destroy all created resources, optional reset if `--reset` used

**Requirements:**
- Docker services running (`make up`) - unless using `--reset`
- Audio fixture: `scripts/fixtures/test.wav` or `scripts/fixtures/test.mp3` (auto-created if missing)
- Backend accessible at `http://localhost:8000`

**Output:**
- `✅ LIVE GO` - All tests passed, system ready (includes Run ID)
- `❌ LIVE NO-GO` - Test failed, shows exact step that failed (includes Run ID)

**Run ID:**
- Each test run gets a unique ID: `LIVE-VERIFY-YYYYMMDD-HHMMSS`
- All created resources include run_id in names for traceability

**Fixture:**
- Default: `scripts/fixtures/test.wav` (minimal WAV file, 144 bytes)
- Alternative: `scripts/fixtures/test.mp3` (if WAV not found)
- To use custom fixture: Replace `scripts/fixtures/test.wav` or `scripts/fixtures/test.mp3` with your file
- Supported formats: WAV, MP3, MP4, AAC, OGG, WebM
- Max size: 200MB

**Example:**
```bash
# Start services
make up

# Run live verification (standard)
make live-verify

# Output:
# Run ID: LIVE-VERIFY-20241223-211500
# ✅ LIVE GO
# All live tests passed!
# System is ready for production use.

# Run with reset (clean environment)
make live-verify-reset
```

**Verification Details:**
- **Manifest verification:** Ensures `manifest.json` doesn't contain forbidden keys (ip/url/filename/path/querystring)
- **Audio encryption:** Verifies `audio.bin` is encrypted (no "RIFF" or "WAVE" headers)
- **Audit hygiene:** Verifies audit events don't contain content or source identifiers
- **Production config:** Tests that invalid config (`DEBUG=false` + `SOURCE_SAFETY_MODE=false`) fails boot

## GO/NO-GO Verification

Before proceeding with new features, run complete verification:

```bash
make verify
```

This runs:
- ✅ Documentation check
- ✅ Source Safety Mode verification
- ✅ Security Freeze v1 verification
- ✅ Log hygiene check
- ✅ Code quality checks
- ✅ Config hard mode verification
- ✅ Full smoke tests (DB up, DB down, No-DB)
- ✅ CI checks (lint, typecheck)

**Result:**
- ✅ **GO**: All verifications pass → Ready for next module
- ❌ **NO-GO**: Any failure → Fix issues before proceeding

**Critical Requirements:**
- No content leakage in logs/audit
- Source protection enforced (SOURCE_SAFETY_MODE forced in prod)
- All destructive operations require confirm + receipt
- Transparency = process, never content
- No AI used in guards or verification

**Guaranteed:**
- Privacy-safe logging (no payloads, headers, IP, URLs, filenames, content)
- Source Safety Mode enforced in production (cannot be disabled)
- Hard mode: SOURCE_SAFETY_MODE=false fails boot in production
- Retention policy as code
- Egress policy documented and verifiable

**Assumed:**
- Docker environment available for testing
- Database available for DB-mode tests
- Network isolation in production (no egress)

**Out of Scope:**
- Authentication/authorization (future module)
- User roles (future module)
- Production deployment automation (infrastructure concern)

## Status

**Version**: 2.0.0  
**Status**: Core foundation complete, ready for modules  
**CORE Freeze**: v1.0.0 (frozen, no changes without ADR/PR)  
**GO/NO-GO**: ✅ Verified and ready
