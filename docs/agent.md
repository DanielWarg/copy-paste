# Agent Entry Point - Copy/Paste

**Detta dokument är OBLIGATORISK läsning för alla AI-assistenter som arbetar i detta repo.**

---

## READ FIRST

**Canonical Documentation (Single Source of Truth):**
1. [SYSTEM_OVERVIEW.md](canonical/SYSTEM_OVERVIEW.md) - Vad systemet är
2. [SECURITY_MODEL.md](canonical/SECURITY_MODEL.md) - Säkerhetsgarantier
3. [MODULE_MODEL.md](canonical/MODULE_MODEL.md) - Hur moduler byggs
4. [DATA_LIFECYCLE.md](canonical/DATA_LIFECYCLE.md) - Datahantering
5. [AI_GOVERNANCE.md](canonical/AI_GOVERNANCE.md) - AI-regler (HUVUDDOKUMENT)
6. [OPERATIONAL_PLAYBOOK.md](canonical/OPERATIONAL_PLAYBOOK.md) - Drift

**Tid:** < 10 minuter för att förstå systemet

---

## Huvudregel

**Säkerhet är absolut. Inga undantag. Inga kompromisser.**

Om du är osäker på om en ändring påverkar säkerheten → **STOPPA OCH FRÅGA** eller läs canonical docs först.

---

## Snabbreferens

**Läs först:**
- `docs/canonical/AI_GOVERNANCE.md` - AI-regler (HUVUDDOKUMENT)
- `docs/canonical/SECURITY_MODEL.md` - Säkerhetsgarantier
- `docs/canonical/MODULE_MODEL.md` - Module Contract

**Kör alltid:**
- `make check-security-invariants` (statisk gate)
- `make verify-brutal` (runtime gate)

**Uppdatera alltid:**
- `docs/canonical/SECURITY_MODEL.md` (om semantik ändras)
- Canonical docs (om systemet ändras)

---

**Detta är en minimal entry point. All detaljerad information finns i canonical docs.**
