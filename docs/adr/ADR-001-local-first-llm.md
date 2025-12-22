# ADR-001: Local-First LLM Strategy

## Status
Accepted

## Context

Vi behöver välja LLM-strategi för Copy/Paste prototypen. Valet påverkar:
- Data-integritet och privacy
- Kostnad
- Latency
- Säkerhet
- Policy compliance

## Decision

Vi väljer **local-first LLM strategy** med Ollama som primär provider.

## Rationale

### Varför lokal LLM?

1. **Policy & Compliance**
   - Journalistisk data är känslig
   - Lokal körning = ingen data lämnar vår infrastruktur
   - Enklare att uppfylla GDPR och policy-krav

2. **Data-integritet**
   - Inga API-calls till externa tjänster
   - Full kontroll över dataflöden
   - Audit trail enklare att implementera

3. **Kostnad**
   - Ingen per-token kostnad
   - Predictable costs (endast infrastruktur)
   - Bra för prototyp och MVP

4. **Säkerhet**
   - Ingen exponering av data till tredje part
   - Lokal körning = färre attack vectors
   - Ollama körs i isolerad Docker network

### När är moln OK?

Moln LLM är acceptabelt när:
- **Opt-in**: Användaren explicit väljer moln
- **Vissa steg**: T.ex. endast för draft-generering, inte för känslig analys
- **Anonymiserad data**: Data är anonymiserad innan skickas till moln

### Hur gör router bytet säkert?

1. **URL Validation**
   - Remote Ollama URLs blockeras som default
   - Kräver explicit `ALLOW_REMOTE_OLLAMA=true` för att aktivera
   - Validering i config

2. **Audit Trail**
   - Alla LLM-anrop loggas med provider
   - Trace IDs för spårning
   - Användare kan se vilken provider som användes

3. **Fallback Strategy**
   - Lokal LLM är default
   - Moln LLM är opt-in
   - Om lokal LLM failar, returnera safe fallback (inte automatiskt moln)

## Consequences

### Positiva

- ✅ Data privacy och integritet
- ✅ Predictable costs
- ✅ Full kontroll
- ✅ Enklare compliance

### Negativa

- ⚠️ Kräver lokal infrastruktur (Ollama)
- ⚠️ Begränsad modell-storlek (8B modeller)
- ⚠️ Latency kan vara högre än moln

### Mitigations

- Ollama körs i Docker (enkel deployment)
- 8B modeller är tillräckliga för prototyp
- Latency acceptabel för batch-processing

## Implementation

- `LocalOllamaProvider`: Primär provider
- `CloudProviderStub`: Disabled by default
- `LLMRouter`: Växlar mellan providers
- Config validation: Blockera remote URLs

## References

- [Ollama Documentation](https://ollama.ai/docs)
- [docs/ARCHITECTURE.md](../ARCHITECTURE.md)
- [docs/SECURITY_OVERVIEW.md](../SECURITY_OVERVIEW.md)

