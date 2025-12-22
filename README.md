# Copy/Paste - Nyhetsdesk Copilot

Produktionsnära prototyp för intern redaktionsapp med RAG, lokal LLM-first (Ollama), säkerhetsramar, och fullständig dokumentation.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (för lokal utveckling)
- Node.js 20+ (för lokal utveckling)
- Ollama (för lokal LLM)

### Lokal Körning

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

### Utveckling

```bash
# Backend (i separat terminal)
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend (i separat terminal)
cd frontend
npm install
npm run dev
```

## Arkitektur

- **Frontend**: Next.js App Router + TypeScript
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL + pgvector
- **LLM**: Ollama (ministral-3:8b)
- **Embeddings**: Ollama (nomic-embed-text)

## Säkerhet

Se [docs/SECURITY_OVERVIEW.md](docs/SECURITY_OVERVIEW.md) för detaljerad säkerhetsdokumentation.

Viktiga säkerhetsfunktioner:
- SSRF-skydd för URL-fetching
- Prompt injection guards
- Output sanitization
- Rate limiting per API-key
- Audit trail för all aktivitet

## Dokumentation

- [Implementation Plan](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security Overview](docs/SECURITY_OVERVIEW.md)
- [Runbook](docs/RUNBOOK_DEV.md)

## License

MIT

