# Threat Model

**Detta dokument är en sammanfattning. För fullständig information, se [security-complete.md](security-complete.md#threat-model).**

## Översikt

Copy/Paste-systemet skyddar mot följande hot:

1. **Källidentifiering** - Attacker försöker identifiera källor genom metadata
2. **Content Leakage** - Känsligt innehåll läcker i logs eller felmeddelanden
3. **Data Exfiltration** - Attacker försöker stjäla känsligt material
4. **Unauthorized Access** - Obefintlig användare får tillgång
5. **PII Leakage to External AI** - Personuppgifter skickas till externa AI-tjänster
6. **Misconfiguration** - Osäker konfiguration gör systemet sårbart

## Detaljerad information

Se [Threat Model-sektionen i security-complete.md](security-complete.md#threat-model) för fullständig beskrivning av varje hot, skyddsåtgärder och verifieringsmetoder.


