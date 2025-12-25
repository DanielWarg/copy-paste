# Repository Path Fix - Eliminera Kolon (:) Permanent

**Datum:** 2025-12-24  
**Problem:** Docker Desktop på macOS/Windows kan inte hantera kolon (`:`) i bind mount paths  
**Impact:** Blockerar `make verify-phase-b-runtime` och alla Docker Compose services

---

## 1. Detektering

### Nuvarande Status

**Kör detta för att detektera problemet:**

```bash
# Kontrollera aktuell path
CURRENT_PATH=$(pwd)
echo "Current path: ${CURRENT_PATH}"

# Detektera kolon
if [[ "$CURRENT_PATH" == *":"* ]]; then
    echo "❌ PROBLEM: Path contains ':' at position(s):"
    echo "$CURRENT_PATH" | grep -ob ":"
    echo ""
    echo "This breaks:"
    echo "  - Docker bind mounts (volume specification)"
    echo "  - docker-compose.prod_brutal.yml (Caddyfile mount)"
    echo "  - All scripts using docker-compose"
    echo "  - make verify-phase-b-runtime"
else
    echo "✅ OK: No colon in path"
fi
```

**Förväntat resultat för detta repo:**
```
Current path: /Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE
❌ PROBLEM: Path contains ':' at position(s):
/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE
```

**Varför detta bryter:**
- Docker Desktop tolkar `:` som separator i volume-specifikationen
- `./Caddyfile.prod_brutal:/etc/caddy/Caddyfile:ro` blir ogiltig när path innehåller `:`
- Error: `invalid volume specification`

---

## 2. Permanent Lösning

### macOS

**Steg 1: Stoppa alla services**
```bash
cd "$(pwd)"
docker-compose -f docker-compose.prod_brutal.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true
```

**Steg 2: Navigera till parent directory**
```bash
cd "$(dirname "$(pwd)")"
# Nuvarande: /Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE
# Efter: /Users/evil/Desktop/EVIL/PROJECT
```

**Steg 3: Rename repository folder**
```bash
# Rename från COPY:PASTE till COPY-PASTE
mv "COPY:PASTE" "COPY-PASTE"
```

**Steg 4: Navigera till ny path**
```bash
cd COPY-PASTE
```

**Steg 5: Verifiera git remote (om nödvändigt)**
```bash
# Kontrollera remote URL
git remote -v

# Om remote URL innehåller kolon, uppdatera:
# git remote set-url origin <new-url-without-colon>
```

**Steg 6: Verifiera path**
```bash
# Kontrollera att kolon är borta
if [[ "$(pwd)" == *":"* ]]; then
    echo "❌ ERROR: Path still contains colon"
    exit 1
else
    echo "✅ OK: Path is clean"
    echo "New path: $(pwd)"
fi
```

**Komplett sekvens (kopiera och kör):**
```bash
# Stoppa services
cd "$(pwd)" && docker-compose -f docker-compose.prod_brutal.yml down 2>/dev/null || true

# Navigera till parent
cd "$(dirname "$(pwd)")"

# Rename
mv "COPY:PASTE" "COPY-PASTE"

# Navigera tillbaka
cd COPY-PASTE

# Verifiera
if [[ "$(pwd)" == *":"* ]]; then
    echo "❌ ERROR: Path still contains colon"
    exit 1
else
    echo "✅ OK: Path fixed"
    echo "New path: $(pwd)"
fi
```

---

### Windows + WSL

**Steg 1: Stoppa alla services (i WSL)**
```bash
cd "$(pwd)"
docker-compose -f docker-compose.prod_brutal.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true
```

**Steg 2: Stäng WSL terminal**

**Steg 3: I Windows Explorer eller PowerShell**
```powershell
# Navigera till parent directory
cd "C:\Users\<user>\Desktop\EVIL\PROJECT"

# Rename folder
Rename-Item -Path "COPY:PASTE" -NewName "COPY-PASTE"
```

**Steg 4: Öppna WSL igen och navigera**
```bash
cd /mnt/c/Users/<user>/Desktop/EVIL/PROJECT/COPY-PASTE
```

**Steg 5: Verifiera path**
```bash
# Kontrollera att kolon är borta
if [[ "$(pwd)" == *":"* ]]; then
    echo "❌ ERROR: Path still contains colon"
    exit 1
else
    echo "✅ OK: Path is clean"
    echo "New path: $(pwd)"
fi
```

**Notera:** WSL paths kan innehålla kolon i Windows-mounts (`/mnt/c/...`), men detta är OK eftersom Docker i WSL använder Linux paths, inte Windows paths.

---

## 3. Validering

### Valideringsscript

**Skapa `scripts/validate_repo_path.sh`:**

```bash
#!/bin/bash
# Validate repository path is safe for Docker

set -e

CURRENT_PATH=$(pwd)

echo "Validating repository path..."
echo "Current path: ${CURRENT_PATH}"
echo ""

# Check for colon
if [[ "$CURRENT_PATH" == *":"* ]]; then
    echo "❌ FAIL: Path contains ':'"
    echo "   This breaks Docker bind mounts"
    echo "   Fix: Rename repository folder to remove ':'"
    exit 1
fi

# Check Docker can access path
if ! docker info &>/dev/null; then
    echo "⚠️  WARNING: Docker not running (cannot test mounts)"
else
    # Test Docker can read path
    if docker run --rm -v "${CURRENT_PATH}:/test:ro" alpine ls /test &>/dev/null; then
        echo "✅ Docker can mount path"
    else
        echo "❌ FAIL: Docker cannot mount path"
        exit 1
    fi
fi

# Check Makefile exists
if [ ! -f "Makefile" ]; then
    echo "❌ FAIL: Makefile not found"
    exit 1
fi

echo "✅ Path validation passed"
```

**Kör validering:**
```bash
bash scripts/validate_repo_path.sh
```

---

## 4. Execution

### Kör Phase B Runtime Verification

**Efter path-fix, kör:**

```bash
make verify-phase-b-runtime
```

**Vad händer:**
1. Pre-flight checks (path, Docker, Node/npm)
2. Frontend build (`npm ci` + `npm run build`)
3. Services start (`docker-compose up -d --build`)
4. Verification (`make verify-phase-b`)
5. Evidence pack generation

**Output-filer:**

**Evidence pack:**
- **Path:** `docs/PHASE_B_RUNTIME_EVIDENCE.md`
- **Innehåll:** Datum/tid, commit hash, testresultat, command log, sign-off checklist
- **Status:** Automatiskt genererad vid varje körning

**Log file:**
- **Path:** `phase_b_verification.log` (repo root)
- **Innehåll:** All stdout/stderr från verification
- **Status:** Append-mode (lägger till vid varje körning)

**Exit codes:**
- **0:** Alla tester PASS → Ready for sign-off
- **1:** Något test FAIL → Review evidence pack och fix issues

**Verifiera resultat:**
```bash
# Kolla exit code
echo $?

# Kolla evidence pack
cat docs/PHASE_B_RUNTIME_EVIDENCE.md

# Kolla log
tail -50 phase_b_verification.log
```

---

## 5. Fail-Safe Förbättring

### Automatisk Guard-Script

**Lösning:** Pre-commit hook som blockerar commits om path innehåller kolon.

**Skapa `.git/hooks/pre-commit`:**

```bash
#!/bin/bash
# Pre-commit hook: Block commits if repo path contains colon

CURRENT_PATH=$(pwd)

if [[ "$CURRENT_PATH" == *":"* ]]; then
    echo "❌ PRE-COMMIT BLOCKED: Repository path contains ':'"
    echo ""
    echo "Current path: ${CURRENT_PATH}"
    echo ""
    echo "This breaks Docker bind mounts and prevents verification."
    echo ""
    echo "FIX:"
    echo "  1. Rename repository folder to remove ':'"
    echo "  2. See: docs/REPO_PATH_FIX.md"
    echo ""
    echo "To bypass (NOT RECOMMENDED):"
    echo "  git commit --no-verify"
    echo ""
    exit 1
fi

exit 0
```

**Installera hook:**
```bash
# Skapa hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook: Block commits if repo path contains colon

CURRENT_PATH=$(pwd)

if [[ "$CURRENT_PATH" == *":"* ]]; then
    echo "❌ PRE-COMMIT BLOCKED: Repository path contains ':'"
    echo ""
    echo "Current path: ${CURRENT_PATH}"
    echo ""
    echo "This breaks Docker bind mounts and prevents verification."
    echo ""
    echo "FIX:"
    echo "  1. Rename repository folder to remove ':'"
    echo "  2. See: docs/REPO_PATH_FIX.md"
    echo ""
    exit 1
fi

exit 0
EOF

# Gör executable
chmod +x .git/hooks/pre-commit

# Testa
.git/hooks/pre-commit
```

**Alternativ: CI/CD Guard**

**Lägg till i `.github/workflows/ci.yml` (om CI finns):**

```yaml
- name: Check repository path
  run: |
    if [[ "${{ github.workspace }}" == *":"* ]]; then
      echo "❌ ERROR: Repository path contains ':'"
      echo "This breaks Docker bind mounts"
      exit 1
    fi
```

**Rekommendation:** Använd pre-commit hook (enklare, blockerar tidigt).

---

## Snabbstart (Efter Fix)

**1. Verifiera path:**
```bash
bash scripts/validate_repo_path.sh
```

**2. Kör verification:**
```bash
make verify-phase-b-runtime
```

**3. Review evidence:**
```bash
cat docs/PHASE_B_RUNTIME_EVIDENCE.md
```

---

**Status:** ✅ Permanent lösning dokumenterad

