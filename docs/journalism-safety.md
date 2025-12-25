# Journalism Safety & Källskydd

**Detta dokument är en sammanfattning. För fullständig information, se [security-complete.md](security-complete.md#journalism-safety--källskydd).**

## Översikt

Copy/Paste-systemet implementerar strikta regler för källskydd och journalistisk säkerhet.

## Huvudprinciper

1. **Minimera Metadata** - Inget som kan identifiera en källa får hamna i logs eller audit trails
2. **Source Safety Mode** - Tvingat till `true` i produktion, kan inte stängas av
3. **Transparens** - Audit trails visar vad som hände, inte vad som sades
4. **Retention Policy** - Inget material sparas längre än nödvändigt
5. **Human-in-the-Loop** - Alla viktiga beslut kräver mänsklig bekräftelse
6. **Secure Delete Policy** - Krypterad radering med receipt-system

## Detaljerad information

Se [Journalism Safety & Källskydd-sektionen i security-complete.md](security-complete.md#journalism-safety--källskydd) för fullständig beskrivning av alla principer och implementationer.

