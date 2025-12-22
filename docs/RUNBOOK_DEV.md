# Runbook - Development

## Lokal Körning

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (för lokal backend-utveckling)
- Node.js 20+ (för lokal frontend-utveckling)
- Ollama (installerat lokalt eller i Docker)

### Quick Start

```bash
# Klona repo
git clone <repo-url>
cd copy-paste

# Kopiera env-fil
cp .env.example .env

# Starta alla tjänster
docker compose up -d

# Verifiera att allt körs
curl http://localhost:8000/health
```

### Backend Development

```bash
cd backend

# Skapa virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Installera dependencies
pip install -r requirements.txt

# Kör migrations
alembic upgrade head

# Starta backend
uvicorn src.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Installera dependencies
npm install

# Starta frontend
npm run dev
```

## First-Run Checklist

### 1. Database Setup

```bash
# Kör migrations
cd backend
alembic upgrade head

# Verifiera att tabeller skapats
psql -h localhost -U copypaste -d copypaste -c "\dt"
```

### 2. Ollama Setup

```bash
# Starta Ollama (om inte i Docker)
ollama serve

# Ladda ner modeller
ollama pull ministral-3:8b
ollama pull nomic-embed-text
```

### 3. API Key Setup

```bash
# Skapa API key i .env
echo "API_KEYS=your-api-key-here" >> .env

# Testa API key
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/api/v1/sources
```

### 4. Smoke Test

```bash
# Health check
curl http://localhost:8000/health

# Ingest test
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"url": "https://example.com"}'

# Index test
curl -X POST http://localhost:8000/api/v1/index \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"source_ids": []}'

# Brief test
curl -X POST http://localhost:8000/api/v1/brief \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"source_ids": ["source-id-here"]}'
```

## Byta LLM-modell

### Via Environment Variable

```bash
# I .env eller docker-compose.yml
OLLAMA_LLM_MODEL=llama3:8b
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Via Ollama

```bash
# Ladda ner ny modell
ollama pull llama3:8b

# Uppdatera .env
OLLAMA_LLM_MODEL=llama3:8b
```

## Felsökning

### Backend startar inte

```bash
# Kolla logs
docker compose logs backend

# Kolla database connection
docker compose exec backend python -c "from src.core.database import engine; engine.connect()"
```

### Ollama svarar inte

```bash
# Kolla Ollama status
curl http://localhost:11434/api/tags

# Kolla Docker logs
docker compose logs ollama
```

### Migrations failar

```bash
# Kolla database connection
psql -h localhost -U copypaste -d copypaste

# Kör migrations manuellt
cd backend
alembic upgrade head --sql  # Preview SQL
alembic upgrade head         # Kör migrations
```

### Frontend kan inte nå backend

```bash
# Kolla CORS settings i backend
# Kolla NEXT_PUBLIC_API_URL i frontend

# Testa backend direkt
curl http://localhost:8000/health
```

## Vanliga Problem

### Port redan används

```bash
# Hitta process som använder porten
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Döda processen eller ändra port i .env
```

### Database connection error

```bash
# Kolla att PostgreSQL körs
docker compose ps postgres

# Kolla connection string i .env
DATABASE_URL=postgresql+psycopg://copypaste:copypaste@postgres:5432/copypaste
```

### Ollama modell saknas

```bash
# Ladda ner modell
ollama pull ministral-3:8b
ollama pull nomic-embed-text

# Verifiera
ollama list
```

## Development Tips

### Hot Reload

- Backend: `--reload` flag i uvicorn
- Frontend: Next.js har hot reload automatiskt

### Debugging

```bash
# Backend debugging
# Sätt breakpoints i VS Code eller använd pdb
import pdb; pdb.set_trace()

# Frontend debugging
# Använd React DevTools och browser DevTools
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Nästa Steg

Se [ARCHITECTURE.md](ARCHITECTURE.md) för arkitekturöversikt och [docs/PLAN.md](PLAN.md) för implementation plan.

