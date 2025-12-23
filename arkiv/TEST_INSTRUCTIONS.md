# Extended System Test Instructions

## Förberedelser

### 1. Starta alla tjänster

Om du använder Docker Compose:
```bash
docker-compose up -d
```

Om du kör lokalt:
```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Scout
cd scout
python scheduler.py

# Terminal 3: Frontend
cd frontend
npm run dev
```

### 2. Verifiera att tjänsterna körs

```bash
# Backend health check
curl http://localhost:8000/health

# Scout health check
curl http://localhost:8001/health
```

### 3. Om Scout endpoints returnerar 404

Scout-servern behöver restartas för att ladda nya endpoints:

**Docker:**
```bash
docker-compose restart scout
```

**Lokalt:**
Stoppa Scout-processen (Ctrl+C) och starta om:
```bash
cd scout
python scheduler.py
```

## Kör testet

```bash
python3 scripts/test_full_system.py
```

## Förväntade resultat

Testet testar:

1. ✅ Backend endpoints (ingest, scrub, draft)
2. ✅ Scout events endpoint
3. ✅ Scout feeds endpoint (GET/POST/PATCH/DELETE)
4. ✅ Scout config status
5. ✅ Scout notifications
6. ✅ Full pipeline integration
7. ✅ Scout → Backend integration

## Felsökning

### Scout endpoints returnerar 404
- Verifiera att Scout-servern körs: `curl http://localhost:8001/health`
- Restarta Scout-servern
- Kontrollera att `scout/api.py` är uppdaterad med nya endpoints

### Config write inte tillåten
- Sätt `SCOUT_ALLOW_CONFIG_WRITE=true` i docker-compose.yml eller env
- Feed CRUD-operationer kommer att misslyckas om detta inte är satt

### Teams notifications fungerar inte
- Sätt `TEAMS_WEBHOOK_URL` i env för att testa notifications
- Testet kommer att visa om Teams är konfigurerad via `/scout/config/status`

