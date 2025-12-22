# Red Team Plan - Defensiv Testplan

## Scope

**Testmiljö**: Isolerad testmiljö (inte produktion)
**Tidsram**: Definieras per testrunda
**Regler**: Defensiva tester, ingen exploitation av produktionssystem

## Testkategorier

### 1. Authentication & Session

**Testdata**: Test API-keys, mock users
**Pass/Fail Kriterier**:
- ✅ Pass: API-key krävs för alla endpoints utom /health
- ✅ Pass: Ogiltiga API-keys avvisas med 401
- ✅ Pass: Rate limiting fungerar per API-key
- ❌ Fail: Endpoints nåbara utan auth
- ❌ Fail: Rate limiting kan bypassas

**Logging**: Alla auth-försök loggas i audit trail

### 2. SSRF Protection

**Testdata**: 
- Private IPs: `http://192.168.1.1`, `http://10.0.0.1`
- Metadata endpoints: `http://169.254.169.254`
- Localhost: `http://localhost`, `http://127.0.0.1`

**Pass/Fail Kriterier**:
- ✅ Pass: Private IPs blockeras
- ✅ Pass: Metadata endpoints blockeras
- ✅ Pass: Endast HTTPS tillåts
- ✅ Pass: Size limits enforced (max 20MB)
- ❌ Fail: Private IPs kan nås
- ❌ Fail: Metadata endpoints exponeras

**Logging**: Alla SSRF-försök loggas med trace ID

### 3. Prompt Injection

**Testdata**: 
- Källtext med instruktioner: "Ignore previous instructions and..."
- Källtext med tool calls: "Execute system command..."
- Källtext med JSON injection

**Pass/Fail Kriterier**:
- ✅ Pass: System prompt ignorerar instruktioner från källor
- ✅ Pass: Schema validation blockerar farliga outputs
- ✅ Pass: Safe fallback aktiveras vid schema fail
- ❌ Fail: Modellen följer instruktioner från källor
- ❌ Fail: Tool calls kan köras

**Logging**: Alla brief-genereringar loggas med output preview

### 4. Output Safety

**Testdata**: 
- LLM output med HTML: `<script>alert('XSS')</script>`
- LLM output med JS: `javascript:alert('XSS')`
- LLM output med event handlers: `onclick=...`

**Pass/Fail Kriterier**:
- ✅ Pass: HTML escaped i output
- ✅ Pass: Script tags removed
- ✅ Pass: Dangerous patterns removed
- ❌ Fail: HTML/JS kan köras i UI
- ❌ Fail: XSS möjligt

**Logging**: Output sanitization loggas

### 5. Rate Limiting & DoS

**Testdata**: 
- Burst requests: 100 requests/sekund
- Stora payloads: 25MB requests
- Concurrent LLM calls: 10 samtidiga

**Pass/Fail Kriterier**:
- ✅ Pass: Rate limit enforced (30 RPM)
- ✅ Pass: Concurrency limit enforced (max 2)
- ✅ Pass: Payload size limits enforced
- ✅ Pass: Next.js RSC DoS protection (CVE-2025-55184 patched)
- ❌ Fail: Rate limit kan bypassas
- ❌ Fail: DoS möjligt

**Logging**: Rate limit violations loggas

### 6. Source Code Exposure

**Testdata**: 
- Malicious RSC requests (CVE-2025-55183)
- Server Actions probing

**Pass/Fail Kriterier**:
- ✅ Pass: Next.js patched (15.1.0+)
- ✅ Pass: Source maps disabled i production
- ✅ Pass: Server Actions validated
- ❌ Fail: Source code kan exponeras

**Logging**: Alla RSC requests loggas

### 7. Ollama Exposure

**Testdata**: 
- Remote Ollama URL: `http://attacker.com:11434`
- Port scanning: Försök nå port 11434

**Pass/Fail Kriterier**:
- ✅ Pass: Remote Ollama URLs blockeras
- ✅ Pass: Ollama port ej exponerad (80/443 endast)
- ✅ Pass: Ollama endast nåbar via Docker network
- ❌ Fail: Ollama exponerad utåt
- ❌ Fail: Remote Ollama kan användas

**Logging**: Ollama URL validation loggas

### 8. Secrets & Configuration

**Testdata**: 
- Secret scanning: Sök efter API keys i kod
- Config exposure: Kolla .env files

**Pass/Fail Kriterier**:
- ✅ Pass: Inga secrets i kod
- ✅ Pass: .env.example utan secrets
- ✅ Pass: "No secrets in logs" policy följs
- ❌ Fail: Secrets exponeras

**Logging**: Secret scanning results

## Testprocess

### Förberedelse

1. **Isolerad miljö**: Sätt upp testmiljö separat från produktion
2. **Testdata**: Förbered icke-känslig testdata
3. **Logging**: Aktivera logging på servern
4. **Backup**: Backup av testdata

### Testrunda

1. **Scope**: Definiera scope för runda
2. **Regler**: Tydliga ROE (Rules of Engagement)
3. **Testning**: Kör tester enligt kategorier ovan
4. **Logging**: Verifiera att allt loggas
5. **Dokumentation**: Dokumentera resultat

### Efter testrunda

1. **Analys**: Analysera resultat mot pass/fail kriterier
2. **Rapport**: Skriv rapport med findings
3. **Remediation**: Åtgärda findings
4. **Verifiering**: Verifiera att åtgärder fungerar
5. **Rollback**: Om nödvändigt, rollback ändringar

## Pass/Fail Kriterier (Sammanfattning)

| Kategori | Pass | Fail |
|----------|------|------|
| SSRF | Block private ranges | Private IPs nåbara |
| Prompt Injection | Inga tool-actions | Tool calls möjliga |
| Output Safety | Ingen osanitized HTML | XSS möjligt |
| Rate Limiting | Limits enforced | Bypass möjligt |
| Ollama | Ej exponerad | Port exponerad |
| Secrets | Inga i kod/logs | Secrets exponerade |

## Säkerhetsåtgärder

- **Isolerad miljö**: Tester körs i isolerad miljö
- **Tydliga ROE**: Rules of Engagement definierade
- **Logging**: Alla tester loggas
- **Rollback**: Möjlighet att rollback ändringar
- **Scope**: Tydlig scope för varje runda

## Reporting

Rapporter ska innehålla:
- Testkategori
- Testdata använd
- Resultat (Pass/Fail)
- Findings
- Rekommendationer
- Remediation plan

