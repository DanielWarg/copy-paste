# Copy/Paste v2 - Arbetsplan

## Projektöversikt
Modulär ombyggnad av Copy/Paste systemet för skalbarhet och enkel deployment på www.postboxen.se. Vi bygger en sak i taget, testar noggrant, och går vidare till nästa del när den är klar.

## Arbetsmetodik
- ✅ **En modul i taget** - Färdigställ och testa innan nästa
- ✅ **Testdriven** - Varje modul måste ha tester och verifieras
- ✅ **Dokumenterad** - Uppdatera denna plan efter varje steg
- ✅ **Commit per modul** - Committa när modulen är klar och testad
- ✅ **Skalbar arkitektur** - Förbered för enkel deployment

## Systemarkitektur - Moduldefinitioner

### Modul 1: Scout (Feed & Kanalövervakning)
**Syfte:** Övervaka RSS-feeds och andra kanaler för ny information

**Funktionalitet:**
- RSS feed polling (intervallbaserad)
- Stöd för andra kanaler (Twitter/X, Mastodon, etc.)
- Deduplicering av innehåll
- Event scoring/prioritering
- Real-time notifikationer vid nya events

**Tekniska krav:**
- Skalbar polling-mekanism
- Persistent lagring av sett innehåll (SQLite/PostgreSQL)
- Konfigurerbar polling-frekvens per feed
- Event scoring baserat på relevans/kritikalitet

**API:**
- `GET /scout/feeds` - Lista alla feeds
- `POST /scout/feeds` - Lägg till ny feed
- `PATCH /scout/feeds/{id}` - Uppdatera feed
- `DELETE /scout/feeds/{id}` - Ta bort feed
- `GET /scout/events` - Hämta events
- `POST /scout/feeds/{id}/poll` - Manuell polling

**Output:** Standardiserade events som skickas till styrmodulen

---

### Modul 2: Transkribering & Databas
**Syfte:** Transkribera audio/video och lagra i sökbar databas

**Funktionalitet:**
- Audio transkribering (Faster-Whisper lokalt)
- Video transkribering (framtida)
- Lagring i relationsdatabas (PostgreSQL)
- Vektordatabas för semantisk sökning (ChromaDB/Pinecone/PostgreSQL pgvector)
- Fulltextsökning
- Metadata-hantering

**Tekniska krav:**
- Lokal transkribering (ingen extern API för audio)
- Strukturerad lagring (transkript, metadata, timestamps)
- Vektorembedding för semantisk sökning
- Indexering för snabb sökning

**API:**
- `POST /transcribe/audio` - Transkribera audio-fil
- `POST /transcribe/video` - Transkribera video (framtida)
- `GET /transcripts` - Sök transkript
- `GET /transcripts/{id}` - Hämta specifikt transkript
- `POST /search/semantic` - Semantisk sökning i vektordatabas

**Output:** Transkript + metadata + embeddings lagrade i databas

---

### Modul 3: GDPR Säkerhetslager
**Syfte:** Anonymisering och GDPR-kompatibel hantering av personuppgifter

**Funktionalitet:**
- Multi-layer anonymisering (regex → LLM → verifiering)
- PII-detektion och masking
- Receipt-system för spårbarhet
- Approval workflow för känslig information
- RAM-only lagring (ingen persistent lagring av känslig data)

**Tekniska krav:**
- Fail-closed beteende (blockera vid osäkerhet)
- Lokal LLM för PII-detektion (Ollama)
- Deterministic verification
- TTL-baserad lagring (RAM-only)

**API:**
- `POST /privacy/scrub` - Anonymisera text
- `GET /privacy/receipt/{event_id}` - Hämta receipt
- `POST /privacy/approve` - Godkänn gated event

**Output:** Anonymiserad text + receipt + approval_token (om nödvändigt)

---

### Modul 4: Styrmodul (Orchestrator/Correlation Engine)
**Syfte:** Övervaka alla moduler och identifiera kopplingar/korrelationer

**Funktionalitet:**
- Real-time övervakning av alla moduler
- Korrelationsdetektion (namn, organisationer, events)
- Cross-reference mellan feeds och databas
- Alert/notification när korrelationer hittas
- Event correlation scoring

**Tekniska krav:**
- Event-driven arkitektur
- Real-time processing
- Vektorsökning för fuzzy matching
- Notification system (Teams, email, etc.)

**API:**
- `GET /orchestrator/status` - Status för alla moduler
- `GET /orchestrator/correlations` - Lista korrelationer
- `POST /orchestrator/watch` - Lägg till watch pattern
- `GET /orchestrator/alerts` - Hämta alerts

**Output:** Korrelationsalerts när matchningar hittas

---

### Modul 5: Backend Core (API Gateway)
**Syfte:** Central API-server som samlar alla moduler

**Funktionalitet:**
- REST API för alla moduler
- Authentication/Authorization
- Rate limiting
- CORS hantering
- Health checks
- Logging och monitoring

**Tekniska krav:**
- FastAPI för REST API
- Modulär struktur (varje modul är separat)
- Enkel deployment (Docker)
- Health endpoints per modul

**API:**
- `GET /health` - System health
- `GET /health/{module}` - Modul-specifik health
- Alla modul-API:er exponeras här

---

### Modul 6: Frontend (Admin Dashboard)
**Syfte:** Web UI för administration och övervakning

**Funktionalitet:**
- Feed administration
- Event viewer
- Correlation alerts
- Privacy receipts viewer
- System status dashboard

**Tekniska krav:**
- React + TypeScript
- Responsive design
- Real-time updates (WebSocket/SSE)
- Enkel deployment

---

## Deployment - www.postboxen.se

### Krav för deployment:
- Docker-baserad deployment
- Enkel start/stop
- Environment variables för konfiguration
- Persistent storage för databaser
- Backup-strategi

### Struktur:
```
postboxen.se/
├── api/          (Backend Core)
├── scout/        (Scout modul)
├── transcribe/   (Transkribering modul)
├── privacy/      (GDPR modul)
├── orchestrator/ (Styrmodul)
└── frontend/     (Admin UI)
```

---

## Status

### Fase 0: Förberedelser
- [x] Arkivera gammal kod
- [x] Stänga ner alla servrar
- [x] Skapa arbetsplan
- [x] Definiera moduler och arkitektur
- [x] Första commit och push

### Fase 1: Backend Core (API Gateway)
- [ ] Projektstruktur
- [ ] FastAPI setup
- [ ] Health endpoints
- [ ] CORS och middleware
- [ ] Testning

### Fase 2: Scout Modul
- [ ] RSS polling
- [ ] Deduplicering
- [ ] Event scoring
- [ ] API endpoints
- [ ] Testning

### Fase 3: Transkribering & Databas
- [ ] Audio transkribering
- [ ] PostgreSQL setup
- [ ] Vektordatabas integration
- [ ] API endpoints
- [ ] Testning

### Fase 4: GDPR Säkerhetslager
- [ ] Multi-layer anonymisering
- [ ] Receipt system
- [ ] Approval workflow
- [ ] API endpoints
- [ ] Testning

### Fase 5: Styrmodul (Orchestrator)
- [ ] Event monitoring
- [ ] Korrelationsdetektion
- [ ] Vektorsökning
- [ ] Alert system
- [ ] API endpoints
- [ ] Testning

### Fase 6: Frontend
- [ ] Grundläggande UI
- [ ] Feed administration
- [ ] Event viewer
- [ ] Correlation alerts
- [ ] Testning

### Fase 7: Deployment
- [ ] Docker setup
- [ ] Environment configuration
- [ ] Deployment scripts
- [ ] Monitoring
- [ ] Testning på postboxen.se

## Anteckningar
- Uppdatera detta dokument efter varje steg
- Markera klar med [x] när modul är färdig och testad
- Lägg till datum och kommentarer vid varje uppdatering
- Varje modul ska vara självständig men integrerad via Backend Core

## Senaste uppdatering
2025-12-23: Moduler definierade. Redo att börja bygga Backend Core.

