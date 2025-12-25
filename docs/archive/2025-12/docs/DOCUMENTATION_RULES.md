<!--
ARCHIVED DOCUMENT
This file is no longer authoritative.
Canonical source of truth: docs/canonical/
-->

# Documentation Rules - Copy/Paste

**Version:** 1.0.0  
**Senast uppdaterad:** 2025-12-25

---

## Syfte

Detta dokument definierar hårda regler för dokumentation i Copy/Paste-repot. Målet är att säkerställa att dokumentation är strukturerad, maskinläsbar och inte duplicerad.

---

## Hårda Regler

### Regel 1: Ingen Duplicering

❌ **Ingen säkerhetsregel får beskrivas i mer än ett canonical-doc**

**Exempel:**
- ❌ FEL: `docs/security-complete.md` och `docs/security.md` beskriver samma invariant
- ✅ RÄTT: Endast `docs/canonical/SECURITY_MODEL.md` beskriver invariants

❌ **Inga moduler får ha egna säkerhetsbeskrivningar**

**Exempel:**
- ❌ FEL: `backend/app/modules/record/README.md` beskriver zero egress
- ✅ RÄTT: `backend/app/modules/record/README.md` länkar till `docs/canonical/SECURITY_MODEL.md`

---

### Regel 2: Alla Docs Länkar Uppåt

✅ **All dokumentation måste länka uppåt till canonical docs**

**Exempel:**
```markdown
⚠️ **REFERENCE DOCUMENT**

Detta dokument är en referens. För canonical information, se:
- [SYSTEM_OVERVIEW.md](canonical/SYSTEM_OVERVIEW.md)
- [SECURITY_MODEL.md](canonical/SECURITY_MODEL.md)
```

---

### Regel 3: Canonical Docs är Enda Källan för AI

✅ **Canonical docs i `docs/canonical/` är enda källan för AI-assistenter**

**Canonical docs:**
- `docs/canonical/SYSTEM_OVERVIEW.md` - Vad systemet är
- `docs/canonical/SECURITY_MODEL.md` - Säkerhetsgarantier
- `docs/canonical/MODULE_MODEL.md` - Hur moduler byggs
- `docs/canonical/DATA_LIFECYCLE.md` - Datahantering
- `docs/canonical/AI_GOVERNANCE.md` - AI-regler
- `docs/canonical/OPERATIONAL_PLAYBOOK.md` - Drift

**AI-assistenter ska:**
1. Läs `docs/agent.md` (entry point)
2. Läs canonical docs i `docs/canonical/`
3. Läs reference docs endast om specifik information behövs

---

### Regel 4: Reference Docs är Tunn

✅ **Reference docs ska vara tunna och länka till canonical docs**

**Struktur:**
```markdown
⚠️ **REFERENCE DOCUMENT**

Detta dokument är en referens. För canonical information, se:
- [SYSTEM_OVERVIEW.md](canonical/SYSTEM_OVERVIEW.md)

## Specifik Information

[Endast specifik information som inte finns i canonical docs]
```

**Ta bort:**
- Duplicerad information från canonical docs
- Generella beskrivningar som finns i canonical docs
- Historisk information (flytta till `docs/archive/`)

---

### Regel 5: Historical Docs Arkiveras

✅ **Historical docs flyttas till `docs/archive/`**

**Exempel:**
- `docs/PHASE_*.md` → `docs/archive/`
- `docs/TEST_RESULTS_*.md` → `docs/archive/`
- `docs/FOUNDATION_DONE.md` → `docs/archive/`

**Rationale:** Historical docs är viktiga för historik men ska inte vara i huvuddokumentationen.

---

## Verifiering

### Automatisk Verifiering

**Kör:**
```bash
make check-docs-integrity
```

**Verifierar:**
- Canonical docs existerar
- Inga andra docs duplicerar security-keywords
- Alla .md länkar till canonical docs
- Inga orphan docs (docs utan länkar)

**Om verifieringen failar → CI failar → ändringen stoppas.**

**Implementation:** Se `scripts/check_docs_integrity.py`

---

## Undantag

### UI-Specifika Docs

**Undantag:** `docs/UI_STYLE_TOKENS.md` och `docs/UI_API_INTEGRATION_REPORT.md` är UI-specifika och behöver inte länka till canonical docs (de är referensdokument för UI-utveckling).

### Versionshistorik

**Undantag:** `CHANGELOG.md` är versionshistorik och behöver inte länka till canonical docs.

---

## Referenser

- **Documentation Map:** `docs/DOCUMENTATION_MAP.md`
- **Canonical Docs:** `docs/canonical/`
- **Executive Summary:** `docs/EXECUTIVE_SUMMARY.md`

---

**Detta är en canonical document. Uppdatera endast om dokumentationsregler ändras.**

