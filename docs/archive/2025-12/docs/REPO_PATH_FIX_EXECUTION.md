<!--
ARCHIVED DOCUMENT
This file is no longer authoritative.
Canonical source of truth: docs/canonical/
-->

# Repository Path Fix - Execution Guide

**Datum:** 2025-12-24  
**Syfte:** Steg-för-steg guide för att fixa kolon-problemet och köra verification

---

## Detektering

**Kör detta för att se problemet:**

```bash
bash scripts/validate_repo_path.sh
```

**Förväntat output:**
```
Validating repository path...
Current path: /Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE

❌ FAIL: Path contains ':'
   This breaks Docker bind mounts
   Fix: Rename repository folder to remove ':'
   See: docs/REPO_PATH_FIX.md
```

**Problemet:**
- Path: `/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE`
- Kolon finns på position: `COPY:PASTE` (mappnamnet)
- Docker tolkar `:` som separator i volume-specifikationen
- Resultat: `invalid volume specification` error

---

## Permanent Lösning (macOS)

### Steg 1: Stoppa services

```bash
# Stoppa alla Docker services
docker-compose -f docker-compose.prod_brutal.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true
```

### Steg 2: Navigera till parent directory

```bash
cd "$(dirname "$(pwd)")"
# Nuvarande: /Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE
# Efter: /Users/evil/Desktop/EVIL/PROJECT
```

### Steg 3: Rename repository folder

```bash
mv "COPY:PASTE" "COPY-PASTE"
```

### Steg 4: Navigera till ny path

```bash
cd COPY-PASTE
```

### Steg 5: Verifiera fix

```bash
bash scripts/validate_repo_path.sh
```

**Förväntat output:**
```
Validating repository path...
Current path: /Users/evil/Desktop/EVIL/PROJECT/COPY-PASTE

✅ Path does not contain colon
✅ Docker can mount path
✅ Makefile exists

✅ Path validation passed - Ready for verification
```

---

## Validering

**Kör validering:**

```bash
bash scripts/validate_repo_path.sh
```

**Kriterier:**
- ✅ Ingen kolon i path
- ✅ Docker kan mounta path
- ✅ Makefile finns

---

## Execution

### Kör Phase B Runtime Verification

**Efter path-fix:**

```bash
make verify-phase-b-runtime
```

**Vad händer (automatiskt):**
1. Pre-flight checks (path, Docker, Node/npm)
2. Frontend build (`npm ci` + `npm run build`)
3. Services start (`docker-compose up -d --build`)
4. Verification (`make verify-phase-b`)
5. Evidence pack generation

**Output-filer:**

**Evidence pack:**
- **Path:** `docs/PHASE_B_RUNTIME_EVIDENCE.md`
- **Innehåll:** 
  - Datum/tid (lokal)
  - Git commit hash
  - Overall result (PASS/FAIL)
  - Individual test results (Phase A, Privacy, Frontend)
  - Full command log
  - Sign-off checklist
- **Status:** Automatiskt genererad vid varje körning

**Log file:**
- **Path:** `phase_b_verification.log` (repo root)
- **Innehåll:** All stdout/stderr från verification (append-mode)
- **Status:** Append vid varje körning

**Exit codes:**
- **0:** Alla tester PASS → Ready for sign-off
- **1:** Något test FAIL → Review evidence pack och fix issues

**Verifiera resultat:**

```bash
# Kolla exit code
echo $?

# Kolla evidence pack
cat docs/PHASE_B_RUNTIME_EVIDENCE.md

# Kolla log (sista 50 raderna)
tail -50 phase_b_verification.log
```

---

## Fail-Safe Förbättring

### Pre-commit Hook (Installerad)

**Hook blockerar commits om path innehåller kolon:**

```bash
# Hook finns i: .git/hooks/pre-commit
# Automatiskt aktiv när git commit körs
```

**Testa hook:**

```bash
# Simulera commit (ska blockeras om path har kolon)
git commit --dry-run -m "test"
```

**Om hook blockerar:**
```
❌ PRE-COMMIT BLOCKED: Repository path contains ':'
...
FIX:
  1. Rename repository folder to remove ':'
  2. See: docs/REPO_PATH_FIX.md
```

**Bypass (INTE REKOMMENDERAT):**
```bash
git commit --no-verify  # Bypass hook (inte rekommenderat)
```

---

## Komplett Sekvens (Kopiera och Kör)

```bash
# 1. Detektera problem
bash scripts/validate_repo_path.sh

# 2. Fix (om problem detekteras)
docker-compose -f docker-compose.prod_brutal.yml down 2>/dev/null || true
cd "$(dirname "$(pwd)")"
mv "COPY:PASTE" "COPY-PASTE"
cd COPY-PASTE

# 3. Verifiera fix
bash scripts/validate_repo_path.sh

# 4. Kör verification
make verify-phase-b-runtime

# 5. Review evidence
cat docs/PHASE_B_RUNTIME_EVIDENCE.md
```

---

**Status:** ✅ Komplett execution guide

