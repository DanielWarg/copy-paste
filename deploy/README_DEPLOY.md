# Deployment Guide - postboxen.se

## Prerequisites

- Server med Docker & Docker Compose
- DNS access för postboxen.se
- SSH access till servern

## Steg-för-steg Deployment

### 1. Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verifiera
docker --version
docker compose version
```

### 2. Clone Repository

```bash
git clone <repo-url>
cd copy-paste
```

### 3. Setup Environment

```bash
# Kopiera example
cp .env.example .env.prod

# Redigera .env.prod med produktion-värden
nano .env.prod
```

**Viktiga variabler**:
```env
PUBLIC_BASE_URL=https://nyhetsdesk.postboxen.se
DEBUG=false
API_KEYS=your-production-api-key-here
POSTGRES_PASSWORD=strong-password-here
CORS_ORIGINS=https://nyhetsdesk.postboxen.se
```

### 4. DNS Setup

Skapa A/AAAA-record:
```
nyhetsdesk.postboxen.se → SERVER_IP
```

Verifiera:
```bash
dig nyhetsdesk.postboxen.se
```

### 5. Start Services

```bash
# Starta med production override
docker compose -f docker-compose.yml -f deploy/compose.prod.yml up -d --build

# Verifiera att alla services körs
docker compose ps
```

### 6. Run Migrations

```bash
# Kör migrations
docker compose exec backend alembic upgrade head

# Verifiera
docker compose exec backend alembic current
```

### 7. Verify Deployment

```bash
# Health check
curl https://nyhetsdesk.postboxen.se/health

# Test API (med API key)
curl -H "X-API-Key: your-api-key" https://nyhetsdesk.postboxen.se/api/v1/sources
```

## Security Verification

### 1. Port Scan

```bash
# Verifiera att endast 80/443 är exponerade
nmap -p 1-65535 nyhetsdesk.postboxen.se

# Förväntat: Endast 80 och 443 öppna
```

### 2. Ollama Verification

```bash
# Försök nå Ollama direkt (ska faila)
curl http://nyhetsdesk.postboxen.se:11434

# Förväntat: Connection refused eller timeout
```

### 3. HTTPS Verification

```bash
# Verifiera HTTPS
curl -I https://nyhetsdesk.postboxen.se

# Förväntat: 200 OK med HTTPS
```

## Troubleshooting

### Caddy fails to start

```bash
# Kolla logs
docker compose logs caddy

# Verifiera Caddyfile
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
```

### Backend fails to connect to database

```bash
# Kolla database connection
docker compose exec backend python -c "from src.core.database import engine; engine.connect()"

# Kolla database logs
docker compose logs postgres
```

### Frontend can't reach backend

```bash
# Kolla network
docker compose exec frontend ping backend

# Kolla backend logs
docker compose logs backend
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.yml -f deploy/compose.prod.yml up -d --build
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

### Backup Database

```bash
# Backup
docker compose exec postgres pg_dump -U copypaste copypaste > backup.sql

# Restore
docker compose exec -T postgres psql -U copypaste copypaste < backup.sql
```

## Rollback

```bash
# Stop services
docker compose -f docker-compose.yml -f deploy/compose.prod.yml down

# Checkout previous version
git checkout <previous-commit>

# Restart
docker compose -f docker-compose.yml -f deploy/compose.prod.yml up -d --build
```

