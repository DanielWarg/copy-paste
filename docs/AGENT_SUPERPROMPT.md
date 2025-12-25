# Agent Superprompt - Copy/Paste

**Detta är en "superprompt" som du kan använda som startregel varje gång ni fortsätter bygga i Copy/Paste-repot.**

**Kopiera och klistra in detta i början av varje ny Cursor-session eller när du byter AI-modell.**

---

## Superprompt Template

```
Du arbetar i Copy/Paste-repot. Säkerhet är absolut. Följ dessa invariants och bevisa dem med körbara checks.

HÅRDA INVARIANTS (får inte brytas):

1. prod_brutal: zero egress. Backend ska inte kunna nå internet via docker network och ensure_egress_allowed() ska blockera alla externa providers.

2. mTLS: Alla HTTPS-requests på 443 kräver klientcertifikat (utan cert ska TLS-handshake faila). Health/ready får endast vara åtkomligt på HTTP (80) för driftmonitoring om det är så konfigurerat.

3. Privacy Gate: Extern egress får endast ske med MaskedPayload. Ingen raw text med PII får nå externa providers. Leak => 422.

4. No-content logging: inga payloads/headers/PII/content i logs. Privacy guard ska skydda detta.

5. Fail-closed: osäker config i prod_brutal ska stoppa boot (t.ex. SOURCE_SAFETY_MODE=false eller cloud API keys satta).

ARBETSSÄTT (måste följas):

A) Läs: docs/agent.md, docs/core.md (Module Contract), docs/security-complete.md, docs/UI_STYLE_TOKENS.md.

B) Gör minsta möjliga ändring.

C) Kör verifiering och uppdatera evidenslogg:
   - make check-privacy-gate
   - make check-security-invariants
   - make verify-brutal (eller make verify-phase-b-runtime)
   - frontend: npm run test:e2e (relevant spec)

D) Om någon invariant behöver ändras: uppdatera docs/security-complete.md så att den exakt matchar implementationen.

OUTPUTKRAV:

- Ändra bara nödvändiga filer.
- Uppdatera docs/UI_API_INTEGRATION_REPORT.md när UI↔API ändras.
- Om du lägger till nya endpoints: lägg till E2E-test och uppdatera säkerhetsdokumentation om semantik påverkas.
- Alla API-anrop i frontend måste gå via frontend/src/api/client.ts (request correlation + typed errors). Inga ad-hoc fetch.
- Behåll UI-stil exakt enligt UI style tokens (ingen ny typography/färg/spacing utan tokens).

MÅL FÖR DENNA ÄNDRING:
[Här skriver du vad ni ska bygga härnäst, t.ex. Projects: skapa projekt, lista projekt, koppla record till projekt, osv.]
```

---

## Användning

1. **Kopiera superprompten ovan**
2. **Ersätt `[Här skriver du...]` med ditt specifika mål**
3. **Klistra in i Cursor som första prompt**

**Exempel:**

```
Du arbetar i Copy/Paste-repot. Säkerhet är absolut. Följ dessa invariants...

[... resten av superprompten ...]

MÅL FÖR DENNA ÄNDRING:
Implementera Projects-modulen: skapa projekt, lista projekt, koppla record till projekt, visa projekt-detail med sektioner (Transkript, Filer, Export).
```

---

## Varför detta fungerar

1. **Maskinläsbart:** Alla invariants är kodade i scripts och testbara
2. **Fail-closed:** Verifieringar stoppar om något är fel
3. **Dokumenterat:** Alla regler finns i docs/ som AI måste läsa
4. **Testbart:** Varje invariant har en körbar check

**Oavsett vilken AI-modell som körs → samma regler, samma checks, samma resultat.**

---

## Uppdateringar

Om nya invariants läggs till:
1. Uppdatera `docs/agent.md` (konstitution)
2. Uppdatera `scripts/check_security_invariants.py` (testbar check)
3. Uppdatera `docs/AGENT_SUPERPROMPT.md` (detta dokument)
4. Uppdatera `docs/security-complete.md` (säkerhetssemantik)

