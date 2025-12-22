# Security Policy

## Reporting Vulnerabilities

Om du hittar en säkerhetsbrist, rapportera den via:

- Email: [security@example.com]
- GitHub Security Advisories: [Länk till GitHub]

**VIKTIGT**: Publicera inte sårbarheter publikt innan de är patched.

## Known Vulnerabilities

### React Server Components (RSC) - Next.js

**CVE-2025-55184** (High Severity - DoS)
- **Beskrivning**: Malicious HTTP requests kan hänga servern och konsumera CPU
- **Påverkan**: Alla versioner som hanterar RSC requests
- **Status**: Patched i Next.js 15.1.0+
- **Åtgärd**: Uppdatera till senaste Next.js version

**CVE-2025-55183** (Medium Severity - Source Code Exposure)
- **Beskrivning**: Malicious HTTP requests kan exponera Server Actions source code
- **Påverkan**: Kan avslöja business logic, men inte secrets om de inte är hårdkodade
- **Status**: Patched i Next.js 15.1.0+
- **Åtgärd**: Uppdatera till senaste Next.js version

**Mitigations implementerade**:
- Server-side API proxy med payload size validation
- Request validation innan forwarding till backend
- Uppdaterad Next.js till senaste patched version
- Source maps disabled i production

## Security Updates

Vi följer säkerhetsuppdateringar för:
- Next.js (React Server Components)
- React
- FastAPI
- PostgreSQL
- Ollama

Se [docs/SECURITY_OVERVIEW.md](SECURITY_OVERVIEW.md) för detaljerad säkerhetsdokumentation.

