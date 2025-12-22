# Demo Script

## Scenario: Analysera en nyhetsartikel

### Steg 1: Ingest URL

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{
    "url": "https://example.com/news-article",
    "source_type": "url"
  }'
```

**Förväntat svar**:
```json
{
  "source_id": "uuid-here",
  "status": "success",
  "message": "Source ingested successfully: https://example.com/news-article"
}
```

### Steg 2: Index Source

```bash
curl -X POST http://localhost:8000/api/v1/index \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{
    "source_ids": ["uuid-from-step-1"]
  }'
```

**Förväntat svar**:
```json
{
  "status": "success",
  "message": "Indexed 5 chunks from 1 sources",
  "indexed_count": 5
}
```

### Steg 3: Generate Brief

```bash
curl -X POST http://localhost:8000/api/v1/brief \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{
    "source_ids": ["uuid-from-step-1"],
    "query": "Vad är huvudpunkterna i artikeln?"
  }'
```

**Förväntat svar**:
```json
{
  "brief": "Artikelns huvudpunkter är...",
  "factbox": [
    {
      "claim": "Påstående 1",
      "citation": "chunk-id-1"
    }
  ],
  "draft": "Utkast till artikel...",
  "open_questions": [
    "Fråga 1",
    "Fråga 2"
  ],
  "citations": [
    {
      "chunk_id": "chunk-id-1",
      "text": "Text preview...",
      "source_id": "source-id",
      "source_url": "https://example.com/news-article"
    }
  ],
  "risk_flags": []
}
```

### Steg 4: List Sources

```bash
curl -X GET http://localhost:8000/api/v1/sources \
  -H "X-API-Key: demo-key-12345"
```

### Steg 5: Query Audit Trail

```bash
curl -X GET "http://localhost:8000/api/v1/audit?operation=brief&limit=10" \
  -H "X-API-Key: demo-key-12345"
```

## Frontend Demo

1. Öppna `http://localhost:3000`
2. Ange URL: `https://example.com/news-article`
3. Klicka "Skapa brief"
4. Se resultat i UI

## Verifiering

### Verifiera SSRF-skydd

```bash
# Försök med private IP (ska blockeras)
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{"url": "http://192.168.1.1"}'

# Förväntat: 400 Bad Request med SSRF error
```

### Verifiera Rate Limiting

```bash
# Skicka 35 requests (över limit på 30 RPM)
for i in {1..35}; do
  curl -X GET http://localhost:8000/api/v1/sources \
    -H "X-API-Key: demo-key-12345"
done

# Förväntat: 429 Too Many Requests efter 30 requests
```

### Verifiera Output Sanitization

```bash
# Generera brief och kolla att output är sanitized
curl -X POST http://localhost:8000/api/v1/brief \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{"source_ids": ["source-id"]}'

# Kolla response - HTML ska vara escaped
```

## Sample Inputs

### Nyhetsartikel
- `https://www.svt.se/nyheter/inrikes/example-article`
- `https://www.dn.se/nyheter/example-article`

### RSS Feed
- `https://feeds.bbci.co.uk/news/rss.xml`

### PDF
- `https://example.com/document.pdf` (kräver PDF parser implementation)

## Troubleshooting

### Ingest failar
- Kolla att URL är HTTPS
- Kolla SSRF logs
- Verifiera att URL är nåbar

### Index failar
- Kolla att source finns
- Kolla Ollama connection
- Verifiera embeddings modell

### Brief generation failar
- Kolla att chunks finns
- Kolla Ollama connection
- Verifiera LLM modell
- Kolla schema validation logs

