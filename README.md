# Copy/Paste - Editorial AI Pipeline

Internal showreel system for editorial AI pipelines. Proves that "vibekodade" AI ideas can be turned into production-grade pipelines.

## Quick Start

```bash
# Start all services
docker compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## Architecture

**Ingest → Process (Privacy Shield) → Source Extracts → Generate (Source-Bound Draft)**

### Modules

1. **Event Ingestion** - Normalizes all inputs (URL, text, PDF) to standardized events
2. **Production Bridge (Privacy Shield)** - Local anonymization using Ollama + Ministral 3B
3. **Source-Bound Draft** - AI-generated drafts with enforced traceability

## Security & GDPR

- **No raw PII to external APIs. Ever.**
- Mapping stored in server RAM only (TTL 15 min), never in client or responses
- External API calls require `is_anonymized=true` ALWAYS, regardless of Production Mode
- Privacy-safe logging only (no PII in logs)

## Environment Variables

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OPENAI_API_KEY=sk-...
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## Development

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Showreel (Under 2 minutes)

1. Ingest source (URL/text)
2. Toggle Production Mode ON
3. Show anonymization (before/after)
4. Generate draft
5. Prove citations (click sentence → highlight source)
6. Block unsupported claims (show policy violations)

