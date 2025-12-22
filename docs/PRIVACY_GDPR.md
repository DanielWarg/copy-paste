# Privacy & GDPR

## Datakategorier

### 1. Source Content
**Beskrivning**: Ingested URLs, PDFs, RSS feeds
**Syfte**: Analys och generering av briefs
**Lagringstid**: Enligt retention policy (se nedan)
**Rättigheter**: Rätt till radering, rätt till åtkomst

### 2. Generated Content
**Beskrivning**: Briefs, drafts, factboxes genererade från källor
**Syfte**: Redaktionsarbete
**Lagringstid**: Enligt retention policy
**Rättigheter**: Rätt till radering, rätt till åtkomst

### 3. Audit Logs
**Beskrivning**: Operation history, trace IDs, user IDs
**Syfte**: Spårbarhet och säkerhet
**Lagringstid**: 90 dagar (konfigurerbart)
**Rättigheter**: Rätt till åtkomst (begränsat av säkerhet)

### 4. Embeddings
**Beskrivning**: Vector representations av content
**Syfte**: Semantic search
**Lagringstid**: Tills source content raderas
**Rättigheter**: Raderas automatiskt vid source deletion

## Syfte med databehandling

- **Journalistik**: Analys av källor för redaktionsarbete
- **Säkerhet**: Audit trail för spårbarhet
- **Funktionalitet**: RAG för brief-generering

## Lagringstid

### Source Content
- **Standard**: 365 dagar
- **Konfigurerbart**: Via environment variable `SOURCE_RETENTION_DAYS`

### Generated Content
- **Standard**: 90 dagar
- **Konfigurerbart**: Via environment variable `GENERATED_RETENTION_DAYS`

### Audit Logs
- **Standard**: 90 dagar
- **Konfigurerbart**: Via environment variable `AUDIT_RETENTION_DAYS`

## Rättigheter

### Rätt till åtkomst
- Användare kan begära åtkomst till sina data
- API: `GET /api/v1/sources?user_id=...`
- API: `GET /api/v1/audit?user_id=...`

### Rätt till radering
- Användare kan begära radering av sina data
- API: `DELETE /api/v1/sources/{id}` (planerat)
- Automatisk radering enligt retention policy

### Rätt till rättelse
- Användare kan uppdatera metadata
- API: `PUT /api/v1/sources/{id}` (planerat)

### Rätt till dataportabilitet
- Export av data i JSON-format
- API: `GET /api/v1/sources/{id}/export` (planerat)

## "Do Not Log" Regler

### Aldrig logga:
- ✅ Rå PII (personnummer, email, telefon)
- ✅ Secrets eller API keys
- ✅ Fullständig output (endast preview)
- ✅ Känslig innehåll i audit logs

### Vad som loggas:
- ✅ Trace IDs
- ✅ User IDs (API keys)
- ✅ Operation types
- ✅ Source IDs
- ✅ Output preview (första 1000 chars)
- ✅ Timestamps

## Data Minimization

- **Source Content**: Lagras endast nödvändigt innehåll
- **Generated Content**: Lagras endast genererat innehåll
- **Audit Logs**: Minimal data för spårbarhet

## Security Measures

- **Encryption**: Data encrypted at rest (PostgreSQL)
- **Access Control**: API-key auth
- **Audit Trail**: Alla operationer loggas
- **Retention**: Automatisk radering enligt policy

## Data Processing Agreement

För produktion, se till att:
1. Data Processing Agreement (DPA) finns
2. Subprocessors dokumenterade
3. Transfer mechanisms för internationella transfers

## Kontakt

För GDPR-frågor, kontakta: [privacy@example.com]

