# Architecture

## Komponentöversikt

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Next.js)                                         │
│ - App Router                                               │
│ - Server-side API proxy                                    │
│ - Safe rendering                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                          │
│ - API endpoints                                            │
│ - Auth middleware                                           │
│ - Rate limiting                                            │
│ - SSRF protection                                          │
└──────┬──────────────────────────────┬───────────────────────┘
       │                              │
       │ Internal                     │ Internal
       ▼                              ▼
┌──────────────────┐        ┌──────────────────────────────┐
│ Ollama (Local)  │        │ PostgreSQL + pgvector        │
│ - LLM inference │        │ - Sources                     │
│ - Embeddings    │        │ - Chunks                      │
│                 │        │ - Audit logs                  │
└──────────────────┘        └──────────────────────────────┘
```

## Trust Boundaries

Se [SECURITY_OVERVIEW.md](SECURITY_OVERVIEW.md) för detaljerad trust boundary-beskrivning.

## Dataflöden

### 1. Ingest Flow

```
User → Frontend → API Proxy → Backend → SSRF Fetcher → URL
                                                          ↓
                                    Source (hash, version) → Database
```

### 2. Index Flow

```
User → Frontend → API Proxy → Backend → Source → Chunking
                                                      ↓
                                    Embeddings → Ollama → Vector Store
```

### 3. Brief Generation Flow

```
User → Frontend → API Proxy → Backend → RAG Service
                                              ↓
                                    Retrieve Chunks → Vector Search
                                              ↓
                                    LLM Generation → Ollama
                                              ↓
                                    Schema Validation → Sanitize → Response
```

## Sekvensdiagram

### Ingest Request

```
User          Frontend        API Proxy      Backend        SSRF Fetcher    Database
 │                │               │              │                 │              │
 │──POST /ingest─>│               │              │                 │              │
 │                │──POST /api───>│              │                 │              │
 │                │   proxy       │──POST /api──>│                 │              │
 │                │               │   /v1/ingest │                 │              │
 │                │               │              │──fetch URL──────>│              │
 │                │               │              │<──content────────│              │
 │                │               │              │──store───────────>│             │
 │                │               │              │<──source_id───────│             │
 │                │               │<──response───│                 │              │
 │<──response─────│               │              │                 │              │
```

### Brief Generation

```
User          Frontend        API Proxy      Backend        RAG Service     Ollama      Database
 │                │               │              │                 │            │            │
 │──POST /brief──>│               │              │                 │            │            │
 │                │──POST /api───>│              │                 │            │            │
 │                │   proxy       │──POST /api──>│                 │            │            │
 │                │               │   /v1/brief  │                 │            │            │
 │                │               │              │──retrieve───────>│            │            │
 │                │               │              │                  │──query────>│            │
 │                │               │              │                  │            │            │
 │                │               │              │                  │<──chunks───│            │
 │                │               │              │──generate───────>│            │            │
 │                │               │              │                  │──prompt───>│            │
 │                │               │              │                  │            │            │
 │                │               │              │                  │<──response─│            │
 │                │               │              │──validate────────│            │            │
 │                │               │              │──sanitize────────│            │            │
 │                │               │<──response───│                 │            │            │
 │<──response─────│               │              │                 │            │            │
```

## Väg till Produktion

### Fase 1: Prototyp (Nuvarande)
- ✅ Lokal körning
- ✅ Docker Compose
- ✅ Grundläggande säkerhet
- ✅ API-key auth

### Fase 2: Pre-Production
- [ ] Deploy till postboxen.se
- [ ] Caddy reverse proxy
- [ ] HTTPS med Let's Encrypt
- [ ] Monitoring & logging
- [ ] Backup strategy

### Fase 3: Production
- [ ] IAM integration
- [ ] Session management
- [ ] Enhanced monitoring
- [ ] Auto-scaling
- [ ] Disaster recovery

## API-struktur

**Rekommerat**: `/api` prefix (inte separat subdomän)

- `POST /api/v1/ingest` - Ingest URL
- `POST /api/v1/index` - Index sources
- `POST /api/v1/brief` - Generate brief
- `GET /api/v1/sources` - List sources
- `GET /api/v1/audit` - Query audit trail
- `GET /health` - Health check

## Teknisk Stack

- **Frontend**: Next.js 15.1.0+ (App Router)
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 16 + pgvector
- **LLM**: Ollama (ministral-3:8b)
- **Embeddings**: Ollama (nomic-embed-text)
- **Reverse Proxy**: Caddy (produktion)

## Deployment

Se [deploy/README_DEPLOY.md](../deploy/README_DEPLOY.md) för deployment-instruktioner.

