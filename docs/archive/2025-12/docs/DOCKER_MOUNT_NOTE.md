<!--
ARCHIVED DOCUMENT
This file is no longer authoritative.
Canonical source of truth: docs/canonical/
-->

# Docker Bind Mount Note - macOS

**Datum:** 2025-12-24  
**Status:** Runtime Blocker  
**Syfte:** Dokumentera Docker bind mount-problem med kolon i repo-path

---

## Problem

**Docker Desktop på macOS** har kända problem med bind mounts när sökvägen innehåller kolon (`:`).

**Symptom:**
```
Error response from daemon: invalid volume specification: 
'/host_mnt/Users/.../COPY:PASTE/Caddyfile.prod_brutal:/etc/caddy/Caddyfile:ro'
```

**Orsak:**
- Docker Desktop tolkar kolon som separator i volume-specifikationen
- Detta gör att bind mounts failar
- Detta blockerar `make verify-brutal` och Phase B runtime-verifiering

---

## Lösning

**Rekommenderad åtgärd:**
Rename repo-mappen så att sökvägen inte innehåller kolon.

**Exempel:**
```bash
# Från:
/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE

# Till:
/Users/evil/Desktop/EVIL/PROJECT/COPY-PASTE
```

**Process:**
1. Stoppa alla Docker services
2. Rename mappen (ta bort kolon)
3. Uppdatera git remote om nödvändigt
4. Starta services igen

---

## Workaround

**Ingen kod-workaround rekommenderas.**

Detta är ett Docker Desktop + macOS-specifikt problem. Bästa lösningen är att undvika kolon i repo-path.

---

## Impact

**Blockerar:**
- `make verify-brutal` (runtime validation)
- `make verify-phase-b` (Phase B verification)
- Alla Docker Compose services som använder bind mounts

**Påverkar inte:**
- Static validation (`scripts/validate_del_a.sh`)
- Kod-implementation
- Dokumentation

---

**Status:** ⚠️ Runtime Blocker - Rename repo-path rekommenderas

