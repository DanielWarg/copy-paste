---
name: Scout RSS Watcher Implementation
overview: Implementera Scout-modulen för RSS-feed monitoring som automatiskt detekterar nya items och skickar dem till den befintliga `/api/v1/ingest` endpointen. Modulen ska vara en separat service som körs i docker-compose, med deduplication och konfigurerbart polling-intervall.
todos:
  - id: scout_structure
    content: "Skapa /scout/ struktur: rss_watcher.py, dedupe_store.py, scheduler.py, feeds.yaml, Dockerfile, requirements.txt"
    status: pending
  - id: dedupe_store
    content: "Implementera dedupe_store.py med SQLite för dedupe-key storage (guid → link → hash ordning, GDPR: endast key + event_id, aldrig innehåll)"
    status: pending
    dependencies:
      - scout_structure
  - id: rss_watcher
    content: "Implementera rss_watcher.py: RSS polling, parse items, beräkna dedupe-key (guid → link → hash), POST till /api/v1/ingest med URL eller fallback-text om länk saknas"
    status: pending
    dependencies:
      - dedupe_store
  - id: scheduler
    content: "Implementera scheduler.py med APScheduler: konfigurerbart polling, enabled/backoff logik, SCOUT_RUN_ONCE flag för demo/CI"
    status: pending
    dependencies:
      - rss_watcher
  - id: feeds_config
    content: Skapa feeds.yaml med exempel-feeds, default_poll_interval (900 sek), och per-feed poll_interval override
    status: pending
    dependencies:
      - scout_structure
  - id: docker_integration
    content: Uppdatera docker-compose.yml med scout service och volumes
    status: pending
    dependencies:
      - scout_structure
  - id: scoring
    content: Implementera optional scoring (lokal heuristik, ingen OpenAI) i scout/scorer.py
    status: pending
    dependencies:
      - rss_watcher
  - id: scout_endpoint
    content: "Implementera GET /scout/events endpoint i Scout service för att lista events från senaste 24h (obligatorisk minimal UI)"
    status: pending
    dependencies:
      - rss_watcher
  - id: frontend_ui
    content: Skapa ScoutEvents.tsx komponent + Scout GET /scout/events endpoint för minimal UI (obligatorisk)
    status: pending
    dependencies:
      - scout_endpoint
  - id: integration_test
    content: "Testa full pipeline: RSS feed → Scout → Ingest → Scrub → Draft"
    status: pending
    dependencies:
      - docker_integration
      - frontend_ui
---

# Scout RSS Watcher - Implementation Plan

## Final Constraints (Non-Negotiable)

1. **Scout fetchar inte artikelinnehåll.** Den postar URL eller fallback-text om länken saknas.
2. **poll_interval är per feed, annars default 15 min.**
3. **dedupe-key order: guid → link → hash(title+published+feed).**
4. **UI ska vara minimal; undvik ny backend-lagring om inte nödvändigt.**

## Översikt

Implementera RSS Watcher som en separat service (`scout/`) som:

- Pollar RSS feeds enligt konfiguration i `feeds.yaml` (per feed `poll_interval` eller default 15 min)
- Respekterar feed `enabled` flag och implementerar exponential backoff vid failures
- Detekterar nya items via deduplication (dedupe-key: guid → link → hash)
- Skickar nya items till `/api/v1/ingest` med `input_type="url"` om länk finns
- Fallback: Om länk saknas/tom → POST med `input_type="text"` (title + description)
- Inkluderar optional scoring (lokal heuristik, ingen OpenAI)
- Producer-only: Scout fetchar ALDRIG artikelinnehåll
- Stödjer `SCOUT_RUN_ONCE=true` för demo/CI (kör ett varv och exit)

## Arkitektur & Data Flow

```
RSS Feed → Scout Service → Dedupe Check → POST /api/v1/ingest → Existing Pipeline
                                    ↓
                            Dedupe Store (SQLite)
```

## Filer att Skapa

### `/scout/rss_watcher.py`

Huvudmodul för RSS polling och item processing:

- Läs `feeds.yaml` konfiguration
- Polla varje feed enligt dess `poll_interval`
- Parse RSS items med `feedparser`
- Beräkna dedupe-key i ordning: `guid` → `link` → `hash(title+published+feed)`
- Kontrollera deduplication via `dedupe_store`
- För nya items:
        - Om item har `link` och den är icke-tom → POST till `/api/v1/ingest` med `input_type="url"` och `value=link`
        - Om item saknar `link` eller länk är tom → POST med `input_type="text"` och `value=title + description` med `partial_content=true` i metadata
- Lägg till `scout_dedupe_key` i metadata för spårbarhet
- Optional scoring: Lägg till `score` i metadata om implementerad

### `/scout/feeds.yaml`

Konfigurationsfil för RSS feeds:

```yaml
# Global default (används om poll_interval saknas per feed)
default_poll_interval: 900  # 15 minuter

feeds:
  - name: "Polisen"
    url: "https://polisen.se/aktuellt/rss/"
    poll_interval: 300  # 5 minuter (override default)
    enabled: true
    score_threshold: 6  # Optional
    
  - name: "SVT Nyheter"
    url: "https://www.svt.se/nyheter/rss.xml"
    # poll_interval saknas → använder default_poll_interval (900)
    enabled: true
```

### `/scout/dedupe_store.py`

Deduplication storage (SQLite):

- Tabell: `seen_items` med kolumner: `dedupe_key`, `feed_url`, `event_id`, `first_seen`, `last_seen`
- Metoder: `is_seen(dedupe_key)`, `mark_seen(dedupe_key, feed_url, event_id)`, `cleanup_old(days=30)`
- Dedupe-key beräknas i ordning: `guid` → `link` → `hash(title+published+feed)`
- GDPR: Lagrar endast dedupe-key och event_id, aldrig innehåll

### `/scout/scheduler.py`

Scheduler för polling (APScheduler eller enkel loop):

- Kör `rss_watcher.poll_all_feeds()` enligt konfiguration
- Respektera feed `enabled` flag (skip disabled feeds)
- Implementera exponential backoff för failed feeds (max 10 failures → backoff)
- Hantera errors gracefully (log, continue, backoff)
- Health check endpoint för monitoring
- `SCOUT_RUN_ONCE=true` env flag → kör ett poll-varv och exit 0 (för demo/CI)

### `/scout/Dockerfile`

Docker image för Scout service:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "scheduler.py"]
```

### `/scout/requirements.txt`

Dependencies:

- `feedparser` eller `rss-parser`
- `httpx` (för POST till backend)
- `apscheduler` eller `schedule`
- `pyyaml` (för feeds.yaml)

## Integration med Befintlig System (KORRIGERAD)

Scout postar alltid till `/api/v1/ingest` och hämtar aldrig artikelinnehåll.

**Om RSS-item har `link` (icke-tom):**

```python
POST http://backend:8000/api/v1/ingest
{
  "input_type": "url",
  "value": "https://article-url.com/..."
}
```

**Om `link` saknas/tom:**

```python
POST http://backend:8000/api/v1/ingest
{
  "input_type": "text",
  "value": "<title>\n\n<description>"  # Kombinera title och description
}
# Metadata ska inkludera: {"partial_content": true, "scout_source": "...", "scout_feed_url": "...", "scout_dedupe_key": "..."}
```

**VIKTIGT:** Scout fetchar ALDRIG artikelinnehåll. Den postar bara URL:en eller fallback-text om länk saknas.

### Event Metadata

När Scout skapar events via `/api/v1/ingest`, lägg till i metadata:

- `scout_source`: feed name
- `scout_feed_url`: RSS feed URL
- `scout_item_url`: artikel-URL (om finns)
- `scout_dedupe_key`: dedupe-key som användes (för spårbarhet)
- `scout_score`: optional score (1-10)
- `scout_detected_at`: timestamp
- `partial_content`: true (endast om fallback-text användes)

## Optional Scoring (Lokal, Ingen OpenAI)

Enkel heuristik i `scout/scorer.py`:

- Keyword matching (t.ex. "breaking", "urgent")
- Feed prioritet (vissa feeds = högre score)
- Item recency (nyare = högre score)
- Returnera score 1-10
- Använd `score_threshold` från feeds.yaml för att filtrera

## Docker Compose Integration

Uppdatera `docker-compose.yml`:

```yaml
services:
  scout:
    build:
      context: ./scout
      dockerfile: Dockerfile
    environment:
      - BACKEND_URL=http://backend:8000
      - FEEDS_CONFIG=/app/feeds.yaml
      - SCOUT_RUN_ONCE=${SCOUT_RUN_ONCE:-false}  # För demo/CI
    volumes:
      - ./scout:/app
      - scout_data:/app/data  # För SQLite dedupe store
    depends_on:
      - backend
    restart: unless-stopped
```

## Frontend UI (Minimal - Obligatorisk)

**Scout egen endpoint (rekommenderat för showreel)**
- Scout exponerar enkel HTTP endpoint: `GET /scout/events?hours=24`
- Returnerar lista från Scout's SQLite: `dedupe_key`, `feed_url`, `event_id`, `detected_at`, `score`
- Frontend: `ScoutEvents.tsx` komponent som visar incoming items (liten lista)
- Ingen ny backend-lagring behövs
- "Wow"-signal utan att röra backend

## Säkerhet & GDPR

- RSS content är untrusted input → behandlas som alla andra inputs
- Dedupe store lagrar endast hash, aldrig innehåll
- Scout bypassar ALDRIG Privacy Shield → alla events går genom `/api/v1/ingest`
- Rate limiting: Scout ska respektera backend rate limits
- Error handling: Scout ska inte crasha vid RSS parse errors

## Testning

- Unit tests: `scout/tests/test_dedupe_store.py`, `test_rss_watcher.py`
- Integration test: Verifiera att events skapas korrekt
- E2E test: Full flow RSS → Ingest → Scrub → Draft

## Definition of Done

- [ ] Scout service körs i docker-compose
- [ ] RSS feeds pollas enligt konfiguration
- [ ] Nya items detekteras och skickas till `/api/v1/ingest`
- [ ] Deduplication fungerar (inga duplicates)
- [ ] Fallback till RSS text (title + description) vid saknad/tom link
- [ ] Optional scoring implementerad
- [ ] Minimal UI via Scout endpoint är på plats (GET /scout/events)
- [ ] Feed enabled/backoff logik implementerad
- [ ] SCOUT_RUN_ONCE flag fungerar för demo/CI
- [ ] Full pipeline fungerar: RSS → Ingest → Scrub → Draft
- [ ] Inga nya säkerhetsrisker introducerade
- [ ] Showreel demo fortfarande under 2 minuter

## Implementation Order

1. Skapa `/scout/` struktur och grundfiler
2. Implementera `dedupe_store.py` (SQLite)
3. Implementera `rss_watcher.py` (polling + POST till ingest med dedupe-key ordning: guid → link → hash)
4. Implementera `scheduler.py` (APScheduler loop)
5. Skapa `feeds.yaml` med exempel-feeds och `default_poll_interval` (900 sek)
6. Uppdatera `docker-compose.yml`
7. Testa integration med backend
8. Implementera optional scoring
9. Implementera minimal UI: Scout GET /scout/events endpoint + ScoutEvents.tsx komponent
10. Implementera feed enabled/backoff logik och SCOUT_RUN_ONCE flag
11. E2E test av full pipeline