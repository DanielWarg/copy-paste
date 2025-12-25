# Operational Playbook - Copy/Paste

**Version:** 1.0.0  
**Status:** Canonical Document (Single Source of Truth)  
**Senast uppdaterad:** 2025-12-25

---

## Start

### Snabbstart (3 kommandon)

```bash
# 1. Starta backend + database
make up

# 2. Starta frontend (i separat terminal)
make frontend-dev

# 3. Öppna webbläsaren
open http://localhost:5174
```

**Detaljerad guide:** Se arkiverad `docs/archive/2025-12/docs/getting-started.md` (reference document)

---

## Verifiering

### Statisk Gate (CI)

```bash
make check-security-invariants
```

**Kör:**
- `check_no_egress_bypass()` - Inga direkta HTTP requests utan `ensure_egress_allowed()`
- `check_no_content_in_logs()` - Inga content/PII i log statements
- `check_mtls_required()` - Caddyfile kräver mTLS på port 443
- `check_zero_egress_network()` - Docker compose har `internal_net` med `internal: true`
- `check_no_cloud_keys_in_prod()` - Inga cloud API keys i prod_brutal env

**Om någon invariant bryts → CI failar → ändringen stoppas.**

### Runtime Gate

```bash
make verify-brutal
```

**Kör:**
- `scripts/verify_no_internet.sh` - Verifierar att backend inte kan nå internet
- `scripts/verify_mtls.sh` - Verifierar mTLS enforcement
- Startup checks - Verifierar fail-closed design

**Om någon invariant bryts → verifieringen failar → deployment stoppas.**

### Health Checks

```bash
make health
```

**Kör:**
- `GET /health` - Alltid 200 (backend är igång)
- `GET /ready` - 200 om DB OK, 503 om DB nere

**Status:**
```bash
make status
```

**Visar:**
- Backend health/ready
- Frontend URL
- Docker container status

---

## Drift

### Logs

```bash
make logs
```

**Visar:**
- Backend logs (stdout)
- PostgreSQL logs (om tillgängligt)

**Privacy-safe:** Logs innehåller endast metadata (counts, ids, format), inga filnamn/content/PII.

### Database

**Migrations:**
```bash
make migrate
```

**Status:**
```bash
docker-compose exec postgres psql -U postgres -d copypaste -c "\dt"
```

**Backup:**
- Se arkiverad `docs/archive/2025-12/docs/getting-started.md` för backup-strategier

### Restart

```bash
make restart
```

**Startar om:**
- Backend container
- PostgreSQL container (om tillgängligt)

---

## Incident Response

### Backend startar inte

**Checklist:**
1. Kolla logs: `make logs`
2. Kolla health: `make health`
3. Kolla container status: `docker-compose ps`
4. Kolla config: `.env` fil (se arkiverad `docs/archive/2025-12/docs/getting-started.md`)

**Vanliga orsaker:**
- Config error (fail-fast validation)
- DB connection timeout (om DB nere)
- Port redan i bruk (ändra port i docker-compose.yml)

### Frontend kan inte ansluta

**Checklist:**
1. Kolla backend: `curl http://localhost:8000/health`
2. Kolla CORS: `grep CORS_ORIGINS .env`
3. Kolla frontend config: `frontend/.env` (VITE_API_BASE_URL)

**Vanliga orsaker:**
- Backend är nere
- CORS-blockering (kontrollera CORS_ORIGINS)
- Fel base URL (kontrollera VITE_API_BASE_URL)

### mTLS-fel

**Checklist:**
1. Kolla cert: Se arkiverad `docs/archive/2025-12/docs/MTLS_BROWSER_SETUP.md`
2. Kolla Caddyfile: `client_auth require_and_verify` på port 443
3. Kolla proxy logs: `docker-compose logs proxy`

**Vanliga orsaker:**
- Certifikat saknas eller är ogiltigt
- Caddyfile konfiguration fel
- Browser cert-installation misslyckades

### Privacy Gate-blockering

**Checklist:**
1. Kolla logs: `make logs` (sök efter "privacy_gate" eller "422")
2. Kolla request: Verifiera att raw text inte skickas
3. Kolla Privacy Shield: `backend/app/modules/privacy_shield/README.md`

**Vanliga orsaker:**
- Raw text skickas till extern LLM (måste passera Privacy Gate)
- PII detekteras efter maskning (fail-closed leak check)
- Privacy Gate konfiguration fel

---

## Recovery

### Database Recovery

**Om DB är korrupt:**
1. Stoppa services: `make down`
2. Ta backup (om möjligt): `docker-compose exec postgres pg_dump -U postgres copypaste > backup.sql`
3. Återställ från backup: `docker-compose exec -T postgres psql -U postgres copypaste < backup.sql`
4. Starta services: `make up`

**Om DB måste rensas:**
1. Stoppa services: `make down`
2. Ta bort volumes: `docker-compose down -v`
3. Starta services: `make up` (skapar ny DB)

### File Storage Recovery

**Om filer är korrupta:**
- Filer är krypterade och lagrade som `{sha256}.bin`
- Om fil saknas: Returnera 404 (fil kan inte återställas)
- Om fil är korrupt: Returnera 500 (dekryptering failar)

**Backup-strategi:**
- Se arkiverad `docs/archive/2025-12/docs/getting-started.md` för backup-strategier

---

## Monitoring

### Health Endpoints

**`GET /health`:**
- Alltid 200 (backend är igång)
- Används för liveness probes

**`GET /ready`:**
- 200 om DB OK eller DB inte konfigurerad
- 503 om DB nere
- Används för readiness probes

### Logs

**Format:**
- JSON (om `LOG_FORMAT=json`)
- Text (om `LOG_FORMAT=text`)

**Privacy-safe:**
- Inga filnamn/content/PII i logs
- Endast metadata (counts, ids, format)

**Aggregation:**
- Logs skickas till stdout (kan aggregeras med log aggregation tools)

---

## Maintenance

### Rotera Secrets

**Princip:**
- Rotera regelbundet (t.ex. var 3:e månad)
- Använd säker secrets manager (t.ex. Docker Swarm secrets, Kubernetes secrets)

**Steg:**
1. Generera ny key: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`
2. Uppdatera secret: `/run/secrets/{secret_name}` (i prod_brutal)
3. Restart services: `make restart`

**Varning:** Rotering av encryption keys kräver re-encryption av alla filer (komplex operation, dokumentera separat).

### Database Migrations

**Princip:**
- Migrations körs automatiskt vid startup (non-blocking)
- Manuell körning: `make migrate`

**Varning:** I produktion bör migrations köras manuellt innan deployment (för att undvika schema drift).

---

## Referenser

- **System Overview:** [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
- **Security Model:** [SECURITY_MODEL.md](./SECURITY_MODEL.md)
- **Getting Started:** Se arkiverad `docs/archive/2025-12/docs/getting-started.md`
- **mTLS Setup:** Se arkiverad `docs/archive/2025-12/docs/MTLS_BROWSER_SETUP.md`

---

**Detta är en canonical document. Uppdatera endast om operativa rutiner ändras.**

