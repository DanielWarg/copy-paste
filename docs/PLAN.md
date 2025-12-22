---
name: Copy/Paste Prototyp
overview: "Bygger en produktionsnära prototyp för intern redaktionsapp med RAG, lokal LLM-first (Ollama), säkerhetsramar, och fullständig dokumentation. Stack: Next.js frontend, FastAPI backend, PostgreSQL+pgvector, Ollama embeddings/LLM, API-key auth. Säkerhet först: trust boundaries, SSRF-skydd, schema-gates, source integrity."
todos:
  - id: project-structure
    content: Skapa projektstruktur (frontend/, backend/, docs/, scripts/, docs/adr/) med alla mappar och grundfiler
    status: pending
  - id: docker-setup
    content: Setup docker-compose.yml med PostgreSQL+pgvector, Ollama, backend, frontend och .env.example med alla obligatoriska variabler
    status: pending
    dependencies:
      - project-structure
  - id: backend-core
    content: FastAPI app med database models (SQLAlchemy), pgvector setup, migrations (Alembic), config management (pydantic-settings) med säkerhetsvalidering
    status: pending
    dependencies:
      - docker-setup
  - id: auth-middleware-early
    content: "API-key auth middleware FÖRST (innan annan funktionalitet): rate limiting per API-key, concurrency limits (max 1-2 parallella LLM calls), audit trail foundation"
    status: pending
    dependencies:
      - backend-core
  - id: ssrf-fetcher-early
    content: "SSRF-skyddad URL fetcher FÖRST: scheme allowlist (https), block private IP ranges, block metadata endpoints (169.254.169.254, etc), max response size (10-20MB), timeout, limited redirects"
    status: pending
    dependencies:
      - backend-core
  - id: security-components
    content: Prompt injection guards, output sanitization, Ollama URL validation (blockera remote URLs), content-type allowlist, payload limits (max filstorlek 10-20MB, max textlängd)
    status: pending
    dependencies:
      - auth-middleware-early
      - ssrf-fetcher-early
  - id: secrets-config
    content: .env.example med dokumenterade obligatoriska variabler, 'No secrets in logs' policy, GitHub Actions secret scanning (gitleaks), Trivy container scanning, Dependabot config
    status: pending
    dependencies:
      - docker-setup
  - id: ingest-pipeline
    content: URL fetcher service (använder SSRF-skyddad fetcher), PDF parser med size limits, RSS parser, text normalisering, chunking, source_hash (hash på råtext), content_version (för URL-ändringar), dedupe på chunks
    status: pending
    dependencies:
      - security-components
  - id: embeddings-vector
    content: EmbeddingProvider interface, OllamaEmbeddingProvider, pgvector integration
    status: pending
    dependencies:
      - backend-core
  - id: llm-provider
    content: LLMProvider interface, LocalOllamaProvider (ministral-3:8b), CloudProviderStub (disabled), LLMRouter, token budget management, STRICT JSON schema-gate (Pydantic validation, fail → safe fallback med citations + fel)
    status: pending
    dependencies:
      - backend-core
  - id: rag-pipeline
    content: "Retriever (top-k semantic search), context builder (tight context), prompt templates (system + user), generation service: brief, factbox, draft, open_questions med citations (chunk-id + text + source)"
    status: pending
    dependencies:
      - embeddings-vector
      - llm-provider
  - id: api-endpoints
    content: Implementera /ingest, /index, /brief, /health, /sources, /audit endpoints
    status: pending
    dependencies:
      - rag-pipeline
      - ingest-pipeline
      - auth-middleware-early
  - id: frontend-ui
    content: "Next.js UI med input form (payload limits: max filstorlek, max textlängd), server-side API proxy (API-key i Next.js route, inte i browser), CORS/CSRF protection, result tabs (Brief/Källor/Utkast/Dubbelkolla), export (copy-to-clipboard, download MD), safe rendering (sanitize all LLM output)"
    status: pending
    dependencies:
      - api-endpoints
  - id: audit-trail
    content: Audit log model och logging service för varje körning
    status: pending
    dependencies:
      - backend-core
  - id: security-docs
    content: "Skapa säkerhetsdokument: SECURITY_OVERVIEW.md (med TRUST BOUNDARIES: Internet/källor=untrusted, Backend=policy enforcement, Ollama=lokal utan auth, DB=system of record), THREAT_MODEL.md (STRIDE), LLM_SECURITY.md (OWASP LLM Top 10), ASVS_MAPPING.md (ASVS 5.0), SECURITY.md (vulnerability reporting), RED_TEAM_PLAN.md (defensiv testplan med blue-team krav: scope+regler, testdata, logging, pass/fail kriterier), PRIVACY_GDPR.md"
    status: pending
  - id: architecture-docs
    content: Skapa ARCHITECTURE.md (med trust boundaries diagram, sekvensdiagram, väg till prod), RUNBOOK_DEV.md, DEMO_SCRIPT.md, AGENT_CONSTITUTION_REFERENCE.md, docs/adr/ADR-001-local-first-llm.md (varför lokal LLM, när moln OK, router-säkerhet)
    status: pending
  - id: agent-rules
    content: Kopiera agent.md från root till .cursor/rules/agent.md (använd oförändrad - den är redan perfekt för detta projekt)
    status: pending
  - id: ci-cd
    content: "GitHub Actions: lint, typecheck, tests, secret scanning, dependency review. Pre-commit hooks"
    status: pending
    dependencies:
      - frontend-ui
  - id: testing
    content: Unit tests, integration tests, security tests med fixtures och mocks
    status: pending
    dependencies:
      - api-endpoints
  - id: demo-validation
    content: Demo-scenario i docs/DEMO_SCRIPT.md och verifiera hela flödet fungerar
    status: pending
    dependencies:
      - frontend-ui
      - testing
  - id: deploy-setup
    content: "Deploy till postboxen.se: DNS (A/AAAA-record), deploy/compose.prod.yml (prod override), deploy/Caddyfile (auto-HTTPS), deploy/README_DEPLOY.md (copy/paste deploy), scripts/deploy.sh (1-kommando deploy)"
    status: pending
    dependencies:
      - frontend-ui
  - id: deploy-security
    content: "Prod guards: endast Caddy exponeras (80/443), DEBUG=false, strikt CORS, rate limit påslaget, max payload limits, Ollama ej nåbar utifrån (port scan verifiering)"
    status: pending
    dependencies:
      - deploy-setup
  - id: deploy-first-run
    content: "First-run checklist: migrations (alembic upgrade head), skapa API-key för demo, skapa admin/test user, smoke-test (health, ingest, index, brief)"
    status: pending
    dependencies:
      - deploy-setup
---

# Copy/Paste - Implementation Plan

## Arkitekturöversikt med Trust Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ UNTRUSTED: Internet/Källor                                 │
│ (URL, PDF, RSS - all input är untrusted)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ TRUST BOUNDARY: Backend (Policy Enforcement Point)         │
│ - SSRF-skydd, content-type allowlist, payload limits       │
│ - Prompt injection guards, output sanitization              │
│ - Rate limiting, concurrency limits                        │
│ - API-key auth, audit trail                                │
└──────┬──────────────────────────────┬───────────────────────┘
       │                              │
       ▼                              ▼
┌──────────────────┐        ┌──────────────────────────────┐
│ Ollama (Local)  │        │ PostgreSQL + pgvector        │
│ - Lokal runtime │        │ - System of Record            │
│ - Ingen auth    │        │ - Audit Trail + Metadata      │
│ - Blockera      │        │ - Source integrity (hash,     │
│   remote URLs   │        │   version, dedupe)            │
└──────────────────┘        └──────────────────────────────┘
```

**Trust Boundaries:**

- **Internet/källor = untrusted**: All input från webben är untrusted
- **Backend = policy enforcement point**: All säkerhetspolicy körs här
- **Ollama = lokal runtime utan auth**: Får aldrig exponeras, blockera remote URLs
- **DB = system of record**: All data spåras här med hash och versionering

## Projektstruktur

```
copy-paste/
├── frontend/              # Next.js App Router
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── types/
├── backend/              # FastAPI
│   ├── src/
│   │   ├── api/         # Endpoints
│   │   ├── core/        # Config, security
│   │   ├── services/    # LLM, RAG, ingest
│   │   ├── models/      # DB models, Pydantic schemas
│   │   └── utils/       # Helpers
│   ├── tests/
│   └── alembic/         # DB migrations
├── docs/                 # All dokumentation
├── scripts/              # Dev/deploy scripts
├── docker-compose.yml
├── .env.example
└── README.md
```

## Implementation Todos

### 1. Projektgrund & Konfiguration

- [x] Skapa projektstruktur (frontend/, backend/, docs/, scripts/)
- [x] Setup Python .venv och requirements.txt
- [x] Setup Next.js med TypeScript
- [x] Docker-compose med PostgreSQL (pgvector), Ollama, backend, frontend
- [x] .env.example med alla konfigurationsvariabler
- [x] README.md med quickstart

### 2. Backend Core Infrastructure

- [x] FastAPI app med CORS, middleware (rate limiting, logging)
- [x] Database models (SQLAlchemy): sources, chunks, embeddings, audit_logs
- [x] pgvector setup och migrations (Alembic)
- [x] Config management (pydantic-settings) med säkerhetsvalidering
- [x] API-key auth middleware (enkel men säker)
- [x] Error handling och logging

### 2.5. Säkerhetskomponenter FÖRST (innan annan funktionalitet)

- [x] **API-key auth middleware**: Rate limiting per API-key, concurrency limits (max 1-2 parallella LLM calls)
- [x] **SSRF-skyddad URL fetcher**: Scheme allowlist (https), block private IP ranges, block metadata endpoints (169.254.169.254, etc), max response size (10-20MB), timeout, limited redirects
- [x] Content-type allowlist för ingest
- [x] Payload limits: max filstorlek (10-20MB), max textlängd
- [x] Prompt injection guards: systemprompt som ignorerar instruktioner från källor
- [x] Output sanitization: escape HTML/JS från LLM output
- [x] Ollama URL validation: blockera remote URLs om inte autentiserad

### 4. Ingest Pipeline (med Source Integrity)

- [x] URL fetcher service (använder SSRF-skyddad fetcher)
- [x] PDF parser (PyPDF2/pdfplumber) med size limits (dependencies i requirements.txt)
- [x] RSS parser (feedparser i requirements.txt)
- [x] Text normalisering och cleaning
- [x] **Source integrity**: source_hash (hash på råtext), content_version (för URL-ändringar)
- [x] Chunking strategy (semantic + size-based)
- [x] **Dedupe på chunks** (förhindra duplicering)
- [x] Error handling och retries

### 5. Embeddings & Vector Store

- [x] EmbeddingProvider interface
- [x] OllamaEmbeddingProvider implementation
- [x] Fallback till sentence-transformers om Ollama saknas
- [x] pgvector integration: store/retrieve embeddings
- [x] Index management och optimization

### 6. LLM Provider & Router (med Schema-Gate)

- [x] LLMProvider interface
- [x] LocalOllamaProvider (ministral-3:8b default)
- [x] CloudProviderStub (disabled by default)
- [x] LLMRouter för att växla mellan providers
- [x] Token budget management
- [x] **STRICT JSON schema-gate**: LLM ska alltid returnera strikt JSON enligt Pydantic schema
- [x] **Schema validation**: Om schema fail → "safe fallback" (UI: visar citations + "kunde inte generera strukturerat svar", Backend: loggar trace_id + sparar audit record, ingen retry-loop som kan DoS:a modellen)
- [x] Response parsing och validation

### 7. RAG Pipeline

- [x] Retriever service (top-k semantic search)
- [x] Context builder (tight context, citations)
- [x] Prompt templates (system + user)
- [x] Generation service: brief, factbox, draft, open_questions
- [x] Citation extraction och linking (chunk-id + text + source)

### 8. API Endpoints

- [x] POST /ingest (URL/PDF/RSS)
- [x] POST /index (trigger indexing)
- [x] POST /brief (RAG generation)
- [x] GET /health
- [x] GET /sources (list)
- [x] GET /audit (query audit trail)

### 9. Frontend (med Säkerhet)

- [x] Next.js setup med App Router
- [x] **Server-side API proxy**: API-key i Next.js route (app/api/proxy/route.ts), inte i browser
- [x] **CORS/CSRF protection**: Konfigurera CORS korrekt, security headers
- [x] UI: Input form (URL/text/file upload) med **payload limits** (max filstorlek, max textlängd)
- [x] "Skapa brief" button och loading states
- [x] Result tabs: Brief,ällor, Utkast, Dubbelkolla (grundläggande UI)
- [x] Citation display (klickbara länkar till källor)
- [x] Export: copy-to-clipboard, download as MD (grundläggande)
- [x] **Safe rendering**: Sanitize all LLM output (escape HTML/JS)

### 10. Audit Trail

- [x] Audit log model (timestamp, user, sources, hash, model, prompt_version, chunks, output)
- [x] Logging service (varje körning)
- [x] Query interface för audit logs
- [x] Retention policy dokumentation

### 11. Dokumentation (kritiskt!)

- [x] **docs/SECURITY_OVERVIEW.md**: Hotbild, dataflöden, **TRUST BOUNDARIES** (Internet/källor=untrusted, Backend=policy enforcement, Ollama=lokal utan auth, DB=system of record)
- [x] **docs/THREAT_MODEL.md**: STRIDE, assets, aktörer, angreppsytor, mitigations
- [x] **docs/LLM_SECURITY.md**: OWASP LLM Top 10 mapping (lista risker och mitigations)
- [x] **docs/ASVS_MAPPING.md**: ASVS 5.0 kontroller (vilka vi uppfyller, vad som återstår)
- [x] **SECURITY.md**: Vulnerability reporting policy
- [x] **docs/RED_TEAM_PLAN.md**: Defensiv testplan med **blue-team krav**: scope+regler, testdata (icke-känslig), logging på servern, tydliga pass/fail kriterier (SSRF: block private ranges; prompt injection: inga tool-actions; output safety: ingen osanitized HTML)
- [x] **docs/PRIVACY_GDPR.md**: Datakategorier, syfte, lagringstid, radering, åtkomst, "do not log" regler
- [x] **docs/ARCHITECTURE.md**: Komponenter, sekvensdiagram, **trust boundaries diagram**, väg till produktion, API-struktur (`/api` eller separat subdomän - rekommenderat `/api`)
- [x] **docs/RUNBOOK_DEV.md**: Lokalt körning, hur man byter LLM-modell, felsökning, first-run checklist (migrations, API-key, smoke-test)
- [x] **docs/DEMO_SCRIPT.md**: Demo-scenario med sample inputs (URL → brief → citations → draft → dubbelkolla)
- [x] **docs/AGENT_CONSTITUTION_REFERENCE.md**: Referens för längre constitution
- [x] **docs/adr/ADR-001-local-first-llm.md**: Varför lokal LLM (policy, journalistik, data-integritet), när moln är OK (opt-in), hur router gör bytet säkert

### 12. Agent Rules & Best Practices

- [x] **Kopiera agent.md från root till .cursor/rules/agent.md** (använd oförändrad - den är redan perfekt)
- [x] Inga placeholders, fulla filer vid ändring
- [x] Tests före PR, säkerhetschecklista före merge
- [x] Output alltid spårbar

### 13. CI/CD & Kvalitet (med Secrets & Config)

- [x] GitHub Actions: lint (ruff, ESLint), typecheck (mypy, tsc), unit tests
- [x] **Secret scanning**: gitleaks (redan nämnt, bekräfta)
- [x] **Container scanning**: Trivy eller motsvarande för Docker images
- [x] **Dependabot**: Konfigurera för automatiska dependency updates
- [x] Dependency review
- [x] Pre-commit hooks (lint, format) - scripts skapade
- [x] SBOM eller dependency lockfiles + update guide
- [x] **.env.example**: Dokumenterade obligatoriska variabler med exakta defaults (PUBLIC_BASE_URL, API_KEY_HEADER, BACKEND_PORT, FRONTEND_PORT, DATABASE_URL, OLLAMA_BASE_URL, OLLAMA_LLM_MODEL, OLLAMA_EMBED_MODEL, MAX_UPLOAD_MB, MAX_TEXT_CHARS, RATE_LIMIT_RPM, LLM_CONCURRENCY), "No secrets in logs" policy

### 14. Testing

- [ ] Unit tests för core services (ingest, RAG, embeddings)
- [ ] Integration tests för API endpoints
- [ ] Security tests (SSRF, injection, output handling)
- [ ] Test fixtures och mocks

### 15. Demo & Validation

- [ ] Sample inputs i docs/DEMO_SCRIPT.md
- [ ] Verifiera att hela flödet fungerar: URL → ingest → index → brief → citations
- [ ] Verifiera säkerhetsfeatures (SSRF block, output sanitization)
- [ ] Verifiera audit trail logging

### 16. Deploy & Domän (postboxen.se)

- [x] Välj subdomän: `nyhetsdesk.postboxen.se` (rekommenderat) eller `copilot.postboxen.se`
- [ ] DNS: A/AAAA-record till serverns publika IP (kräver server access)
- [x] Lägg till `deploy/compose.prod.yml` (prod override med restart: unless-stopped, endast Caddy har ports 80/443)
- [x] Lägg till `deploy/Caddyfile` (auto-HTTPS reverse proxy, säkra headers, gzip/zstd, rate limiting headers)
- [x] Lägg till `deploy/README_DEPLOY.md` (copy/paste deploy: install docker, clone repo, sätt .env.prod, docker compose up)
- [x] Lägg till `scripts/deploy.sh` (1-kommando deploy: git pull, build, migrations, restart)
- [x] Säkerställ att endast Caddy exponeras (80/443). Inga andra ports.
- [x] Prod guards:
  - [x] `DEBUG=false`
  - [x] Strikt CORS (endast din domän)
  - [x] Rate limit påslaget
  - [x] Max payload limits påslaget
- [x] First-run checklist:
  - [x] Skapa API-key för demo (dokumenterat i .env.example)
  - [x] Skapa admin/test user (om ni loggar user-id via header) - API-key baserat
  - [x] Verifiera att Ollama ej är nåbar utifrån (port scan) - dokumenterat i deploy/README_DEPLOY.md
  - [x] Kör migrations: `alembic upgrade head` - dokumenterat
  - [x] Smoke-test: `GET /health`, `POST /ingest`, `POST /index`, `POST /brief` - dokumenterat i DEMO_SCRIPT.md

## Tekniska Val (bekräftade)

- **Vector Store**: pgvector (PostgreSQL extension)
- **Embeddings**: Ollama embeddings API (`nomic-embed-text` default, fallback: sentence-transformers)
- **Auth**: Enkel API-key (för demo, redo för red team)
- **LLM**: Ollama ministral-3:8b (default)
- **Frontend**: Next.js App Router + TypeScript
- **Backend**: FastAPI + SQLAlchemy + Alembic

## Säkerhetsfokus (Uppdaterat)

1. **Trust Boundaries**: Tydlig separation mellan untrusted (Internet/källor), policy enforcement (Backend), lokal runtime (Ollama), och system of record (DB)
2. **SSRF-skydd**: URL fetcher med hårda begränsningar (scheme allowlist, private IP block, metadata endpoint block, size/timeout limits)
3. **Prompt injection**: Systemprompt + output sanitization + schema-gate (strikt JSON validation)
4. **Ollama exposure**: Blockera remote URLs, dokumentera localhost saknar auth, aldrig exponera porten
5. **Source integrity**: Hash, versionering, dedupe för spårbarhet och kostnadskontroll
6. **Audit trail**: Logga allt för spårbarhet (timestamp, user, sources, hash, model, prompt_version, chunks, output)
7. **Output safety**: Inga farliga HTML/JS från LLM (sanitize all output)
8. **Rate limiting**: Per API-key, concurrency limits (max 1-2 parallella LLM calls)
9. **API-key security**: Server-side proxy i Next.js, aldrig i browser
10. **Secrets & Config**: Explicit policy, "No secrets in logs", container scanning

## Nästa Steg (Prioriterad Ordning)

Efter planbekräftelse:

1. Skapa projektstruktur (inkl. docs/adr/)
2. Setup docker-compose och dependencies (.env.example med obligatoriska variabler)
3. Implementera backend core (DB models med source_hash, content_version)
4. **Implementera säkerhetskomponenter FÖRST**: Auth + rate limit + SSRF fetcher (innan annan funktionalitet)
5. Secrets & Config policy (no secrets in logs, scanning)
6. Ingest pipeline med source integrity (hash, versionering, dedupe)
7. LLM provider med strikt JSON schema-gate
8. Bygg RAG pipeline
9. Frontend med server-side API proxy (API-key säkert)
10. Dokumentation (med trust boundaries, ADR-001)
11. CI/CD och tester (inkl. container scanning)
12. Demo & validation

## Viktiga Justeringar från Feedback

✅ **Trust Boundaries**: Tydlig separation i SECURITY_OVERVIEW + ARCHITECTURE

✅ **Säkerhet först**: Auth + rate limit + SSRF fetcher implementeras TIDIGT

✅ **Payload limits**: Frontend + backend (max filstorlek, max textlängd)

✅ **Secrets & Config**: Explicit policy, scanning, "No secrets in logs"

✅ **Strikt JSON schema-gate**: LLM output valideras hårt, fail → safe fallback

✅ **Source integrity**: Hash, versionering, dedupe för spårbarhet

✅ **Red team-plan**: Blue-team krav med pass/fail kriterier

✅ **API-key säkert**: Server-side proxy i Next.js, inte i browser

✅ **SSRF metadata**: Blockera metadata endpoints (169.254.169.254, etc)

✅ **ADR-001**: Local-first LLM strategy dokumenterad

✅ **Agent.md**: Används oförändrad från root (redan perfekt)

## Deploy till postboxen.se (enkel, säker, proffsig)

### Mål

- Kunna köra hela stacken på din server bakom **HTTPS** på `nyhetsdesk.postboxen.se` (eller `copilot.postboxen.se`)
- **Inga interna portar exponerade** (varken Ollama, Postgres eller backend)
- Enkel deploy: `git pull` + `docker compose up -d --build`

### Hosting-strategi (rekommenderad)

**Caddy som reverse proxy** (auto-HTTPS, enkelt, stabilt).

Alternativ: Nginx. Men Caddy ger snabbast "shina".

### Public/Private ports (policy)

- Exponera endast:
  - `80/443` → Caddy
- Internt nät (docker network):
  - frontend (Next)
  - backend (FastAPI)
  - postgres (pgvector)
  - ollama
- Backend pratar med Ollama och DB **endast via interna service-namn**.

### DNS

- Skapa A/AAAA-record:
  - `nyhetsdesk.postboxen.se` → serverns publika IP
- (Valfritt) `api.nyhetsdesk.postboxen.se` om du vill separera.

### Nya filer (praxis)

#### 1) `deploy/compose.prod.yml`

Production override:

- `restart: unless-stopped`
- endast Caddy har ports 80/443
- `profiles` eller separata compose-filer för dev/prod
- `env_file: .env.prod` (ej i git)

#### 2) `deploy/Caddyfile`

- Reverse proxy till frontend (och ev backend under `/api`)
- Säkra headers
- Gzip/zstd
- Rate limiting kan ligga i backend, men headers här är bra.

#### 3) `deploy/README_DEPLOY.md`

Steg-för-steg deploy:

- install docker
- clone repo
- sätt `.env.prod`
- `docker compose -f docker-compose.yml -f deploy/compose.prod.yml up -d --build`
- verify: `curl https://nyhetsdesk.postboxen.se/health` (eller motsv)

#### 4) `scripts/deploy.sh` (valfritt men snyggt)

- drar senaste main
- bygger om
- kör migrations
- restart

### Säkerhetsnotis (kritisk)

**Ollama har ingen auth lokalt** → därför:

- Ollama får aldrig exponeras ut på internet
- Backend måste vara enda vägen
- Caddy/Nginx ska aldrig proxya `:11434`

## Execution Gates: 5 saker som gör planen körbar utan stopp

### 1) Definiera exakta defaults i `.env.example`

Lägg in faktiska variabelnamn + default-värden (så teamet inte gissar):

- `PUBLIC_BASE_URL=https://nyhetsdesk.postboxen.se`
- `API_KEY_HEADER=X-API-Key`
- `BACKEND_PORT=8000` `FRONTEND_PORT=3000`
- `DATABASE_URL=postgresql+psycopg://user:pass@postgres:5432/copypaste`
- `OLLAMA_BASE_URL=http://ollama:11434` (prod) + `http://host.docker.internal:11434` (dev)
- `OLLAMA_LLM_MODEL=ministral-3:8b`
- `OLLAMA_EMBED_MODEL=nomic-embed-text` (eller annan faktisk modell från Ollama)
- `MAX_UPLOAD_MB=20` `MAX_TEXT_CHARS=20000`
- `RATE_LIMIT_RPM=30` `LLM_CONCURRENCY=2`

Utan detta blir det alltid friktion.

### 2) Bestäm en embeddings-modell **nu**

Ni har "Ollama embeddings API" – bra, men välj modellnamn.

Annars fastnar ni när ni ska indexera första gången.

**Val**: `nomic-embed-text` (eller ange exakt vilken ni använder i v1).

### 3) Bestäm var API:t lever: "/api" eller separat subdomän

För enkel deploy på postboxen.se:

- Antingen: Caddy proxar `/api/*` → backend
- Eller: `api.nyhetsdesk.postboxen.se` → backend

**Val**: **`/api`** i början för enkelhet (rekommenderat).

### 4) Migrations & first-run

Lägg in "first-run" i RUNBOOK_DEV + deploy-runbook:

- `alembic upgrade head`
- skapa initial API-key (eller läs från env)
- smoke-test:
  - `GET /health`
  - `POST /ingest` med en liten URL
  - `POST /index`
  - `POST /brief`

Utan "first-run" blir det lätt att någon tror att "docker up" räcker.

### 5) "Safe mode" beteende måste vara beskrivet

När schema-gate failar: exakt vad händer?

Skriv:

- UI: visar citations + "kunde inte generera strukturerat svar"
- Backend: loggar trace_id + sparar audit record
- Ingen retry-loop som kan DoS:a modellen

Det är en detalj som gör att ni inte får konstiga demo-fails.

