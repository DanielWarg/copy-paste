# Threat Model

## Assets

1. **Source Content**: Ingested URLs, PDFs, RSS feeds
2. **Embeddings**: Vector representations of content
3. **LLM Output**: Generated briefs, drafts, factboxes
4. **Audit Logs**: Operation history and traceability
5. **API Keys**: Authentication credentials
6. **Source Code**: Application code (Server Actions)

## Actors

1. **Legitimate Users**: Journalists using the system
2. **Attackers**: External malicious actors
3. **Insiders**: Authorized users with malicious intent

## Attack Surfaces

### 1. URL Ingest Endpoint
- **Threat**: SSRF attacks
- **Mitigation**: Scheme allowlist, IP blocking, metadata endpoint blocking

### 2. LLM Generation
- **Threat**: Prompt injection
- **Mitigation**: System prompt ignores source instructions, schema validation

### 3. Next.js RSC Endpoints
- **Threat**: CVE-2025-55184 (DoS), CVE-2025-55183 (Source Code Exposure)
- **Mitigation**: Updated Next.js, request validation, payload limits

### 4. Ollama Exposure
- **Threat**: Unauthorized access to LLM
- **Mitigation**: Local only, URL validation, no port exposure

### 5. Rate Limiting Bypass
- **Threat**: DoS attacks
- **Mitigation**: Per-API-key limits, concurrency limits

## STRIDE Analysis

### Spoofing
- **Threat**: Fake API keys
- **Mitigation**: API key validation, server-side proxy

### Tampering
- **Threat**: Modified source content
- **Mitigation**: Source hashing, version tracking

### Repudiation
- **Threat**: Denial of actions
- **Mitigation**: Comprehensive audit trail

### Information Disclosure
- **Threat**: Source code exposure (CVE-2025-55183)
- **Mitigation**: Patched Next.js, source maps disabled

### Denial of Service
- **Threat**: CVE-2025-55184, rate limit bypass
- **Mitigation**: Rate limiting, concurrency limits, payload limits

### Elevation of Privilege
- **Threat**: Unauthorized Ollama access
- **Mitigation**: Local only, URL validation

## Mitigations Summary

| Threat | Mitigation | Status |
|--------|------------|--------|
| SSRF | URL validation, IP blocking | ✅ Implemented |
| Prompt Injection | System prompt, schema validation | ✅ Implemented |
| DoS (RSC) | Next.js patch, rate limiting | ✅ Implemented |
| Source Code Exposure | Next.js patch, source maps disabled | ✅ Implemented |
| Ollama Exposure | Local only, URL validation | ✅ Implemented |
| Rate Limit Bypass | Per-API-key limits | ✅ Implemented |

## Red Team Test Plan

See [docs/RED_TEAM_PLAN.md](RED_TEAM_PLAN.md) for defensive test plan.

