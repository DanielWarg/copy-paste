# Starta Copy/Paste lokalt

## Snabbstart

```bash
# 1. Kopiera env-fil
cp .env.example .env

# 2. Starta alla services
docker compose up -d

# 3. Vänta tills alla services är klara (30-60 sekunder)
docker compose ps

# 4. Kör migrations
docker compose exec backend alembic upgrade head

# 5. Öppna i browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Testa API direkt

```bash
# Health check (ingen auth krävs)
curl http://localhost:8000/health

# Ingest URL (kräver API key)
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{"url": "https://www.example.com", "source_type": "url"}'

# List sources
curl -H "X-API-Key: demo-key-12345" http://localhost:8000/api/v1/sources
```

## Frontend

Öppna http://localhost:3000 i browser och:
1. Ange URL (t.ex. https://www.example.com)
2. Klicka "1. Ingest URL"
3. Klicka "2. Index" när ingest är klar
4. Klicka "3. Generate Brief" när index är klar

## Felsökning

### Backend startar inte
```bash
docker compose logs backend
```

### Frontend startar inte
```bash
docker compose logs frontend
```

### Ollama svarar inte
```bash
docker compose logs ollama
# Kontrollera att modellen är nedladdad:
docker compose exec ollama ollama list
```

### Database connection error
```bash
# Kolla att postgres körs
docker compose ps postgres
# Testa connection
docker compose exec backend python -c "from src.core.database import engine; engine.connect()"
```

## Stoppa allt

```bash
docker compose down
```

## Rensa allt (inklusive data)

```bash
docker compose down -v
```

