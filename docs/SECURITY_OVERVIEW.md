# Security Overview

## Trust Boundaries

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

## Security Controls

### 1. SSRF Protection
- **URL Fetcher**: Scheme allowlist (HTTPS only)
- **IP Blocking**: Private IP ranges blocked
- **Metadata Endpoints**: Cloud metadata endpoints blocked (169.254.169.254)
- **Size Limits**: Max 20MB response size
- **Timeouts**: 30s timeout on requests
- **Redirect Limits**: Max 5 redirects

### 2. Prompt Injection Protection
- **System Prompt**: Explicitly ignores instructions from sources
- **Output Sanitization**: All LLM output sanitized
- **Schema Validation**: Strict JSON schema-gate with safe fallback

### 3. Rate Limiting & DoS Protection
- **Per API-Key**: 30 requests per minute (configurable)
- **Concurrency Limits**: Max 2 concurrent LLM calls per API-key
- **Payload Limits**: Max 20MB upload, 20k characters text
- **Next.js RSC**: Patched against CVE-2025-55184 (DoS)

### 4. Authentication & Authorization
- **API-Key Auth**: Simple but effective for prototype
- **Server-Side Proxy**: API keys never exposed to browser
- **Audit Trail**: All operations logged with trace IDs

### 5. Output Safety
- **HTML Escaping**: All LLM output escaped
- **XSS Protection**: Script tags and dangerous patterns removed
- **Safe Rendering**: Frontend sanitizes all content

### 6. Source Code Protection
- **Next.js RSC**: Patched against CVE-2025-55183 (Source Code Exposure)
- **Server Actions**: Validated and rate-limited
- **Source Maps**: Disabled in production

### 7. Ollama Security
- **Local Only**: Ollama runs locally, no auth
- **URL Validation**: Remote Ollama URLs blocked
- **No Exposure**: Ollama port never exposed to internet
- **Documentation**: Clearly documented in architecture

## Data Flow Security

1. **Ingest**: URL → SSRF validation → Fetch → Hash → Store
2. **Index**: Source → Chunk → Embed → Vector Store
3. **Brief**: Query → Retrieve → LLM → Schema Validate → Sanitize → Return

## Known Vulnerabilities

### React Server Components (Next.js)
- **CVE-2025-55184**: DoS via malicious RSC requests (Patched in Next.js 15.1.0+)
- **CVE-2025-55183**: Source code exposure via Server Actions (Patched in Next.js 15.1.0+)

**Mitigations**:
- Next.js updated to latest patched version
- Server-side request validation
- Payload size limits
- Rate limiting

## Security Monitoring

- **Audit Trail**: All operations logged
- **Trace IDs**: Every request has trace ID
- **Error Logging**: Errors logged with trace IDs (no secrets)

## Incident Response

1. Identify vulnerability
2. Assess impact
3. Patch or mitigate
4. Update documentation
5. Notify users if needed

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

