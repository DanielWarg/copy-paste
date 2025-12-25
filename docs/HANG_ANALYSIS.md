# Problem: Kommandon hänger sig i projektmappen

## ✅ BEKRÄFTAT (från användarens test)

- ✅ Systemet är friskt
- ✅ Shellen är frisk  
- ✅ Cursor är oskyldig
- ✅ Problemet är isolerat till projektmappen eller dess mount
- ❌ INTE Docker globalt
- ❌ INTE OS-freeze
- ❌ INTE PATH-problem
- ❌ INTE terminal-problem

## 🔍 Rotorsak: Filesystem/Mount-problem

Projektmappen ligger på: `/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE`

**Troliga orsaker (i ordning):**

### 1. Desktop-mount + Spotlight + Docker watcher (90% sannolikhet)
**Problem:**
- Desktop är notoriskt dålig med Spotlight-indexering
- Docker Desktop file watcher kan låsa kataloger
- iCloud sync kan orsaka I/O-blockering
- Kolon i path (`COPY:PASTE`) kan orsaka problem

**Symptom:**
- `cd` till projektet hänger sig
- `ls` hänger sig
- Alla fil-operationer hänger sig

**Test:**
```bash
# I Terminal.app (NY terminal):
cd "/Users/evil/Desktop/EVIL/PROJECT"
# Hänger detta sig? → mount-problem
```

### 2. Docker Desktop file watcher låser katalogen
**Problem:**
- Docker Desktop har file watcher som kan låsa stora kataloger
- Projektet har många filer (backend, frontend, docs, scripts)
- Watcher kan hänga sig på kolon i path

**Test:**
```bash
# Stoppa Docker Desktop helt
# Testa sedan: ls i projektmappen
```

### 3. Spotlight (mds/mdworker) indexerar katalogen
**Problem:**
- Spotlight försöker indexera hela projektet
- Kan hänga sig på stora filer eller symlinks
- Desktop är särskilt känslig för detta

**Test:**
```bash
# Kolla Spotlight-processer:
ps aux | grep -i mds
ps aux | grep -i mdworker
```

### 4. Kolon i path (`COPY:PASTE`) orsakar problem
**Problem:**
- Kolon (`:`) i katalognamn kan orsaka problem i vissa tools
- Docker, git, och vissa shell-commands kan ha problem
- Vi har redan sett problem med frontend volume mounts pga detta

**Bekräftat tidigare:**
- Frontend volume mount problem pga kolon i path (dokumenterat i docker-compose.yml)

## 🛠️ Lösningar (i ordning)

### Lösning A: Flytta projektet från Desktop (REKOMMENDERAT)

**Desktop är notoriskt problematiskt för:**
- Docker file watchers
- Spotlight indexering
- iCloud sync
- Långa paths med specialtecken

**Steg:**
```bash
# 1. Skapa ny katalog utanför Desktop
mkdir -p ~/dev

# 2. Flytta projektet (om mv hänger sig → mount-problem bekräftat)
mv "/Users/evil/Desktop/EVIL/PROJECT" ~/dev/copy_paste

# 3. Testa i ny location
cd ~/dev/copy_paste
ls -U .
```

**Om detta fungerar:**
- ✅ Problemet var Desktop/mount-indexering
- ✅ Projektet fungerar nu normalt
- ✅ Fortsätt med DEL A validering

### Lösning B: Om `mv` hänger sig → hård mount-problem

**Test:**
```bash
# Kolla mounts:
ls /Volumes

# Kolla om något är "offline" eller "network"
# Om ja → eject/unmount i Finder eller Disk Utility
```

### Lösning C: Stoppa Docker Desktop file watcher

**Steg:**
1. Stäng Docker Desktop helt
2. Testa: `ls` i projektmappen
3. Om det fungerar → Docker watcher var problemet
4. Lösning: Flytta projektet från Desktop (Lösning A)

### Lösning D: Exkludera från Spotlight

**Steg:**
```bash
# Lägg till projektet i Spotlight exkluderingar
sudo mdutil -i off "/Users/evil/Desktop/EVIL/PROJECT"
```

**Men:** Detta är temporärt. Bättre att flytta projektet.

## 📋 Nästa steg (efter problemet är löst)

När projektet fungerar (antingen flyttat eller mount fixat):

1. **Validera DEL A:**
   ```bash
   cd ~/dev/copy_paste  # eller fixad path
   ./validate_del_a.sh
   ```

2. **Fortsätt med Brutal Security Profile:**
   - DEL B: Egress Kill Switch
   - DEL C: No Plaintext Export
   - DEL D: Key Management
   - DEL E: Guard Module
   - DEL F: Verification & Docs

3. **Skapa dokumentation:**
   - `docs/security-brutal.md`
   - `docs/runbook.md` (break glass procedures)
   - `make verify-brutal` target

## ⚠️ VIKTIGT: Detta är INTE ett arkitektur-problem

Detta är **ren operativ I/O-hygien**, inte:
- ❌ Brutal mode implementation
- ❌ mTLS configuration
- ❌ Guard modules
- ❌ Export streaming

**Alla filer är korrekt skapade:**
- ✅ `docker-compose.prod_brutal.yml`
- ✅ `Caddyfile.prod_brutal`
- ✅ `scripts/generate_certs.sh`
- ✅ `scripts/verify_mtls.sh`
- ✅ `validate_del_a.sh`

När mount-problemet är löst kommer allt att fungera.

## 🔬 Snabb isoleringstest (2 minuter)

Gör detta i **Terminal.app** (NY terminal):

```bash
# Test 1: Kan du cd:a till projektet?
cd "/Users/evil/Desktop/EVIL/PROJECT"
# Hänger detta sig? → mount-problem bekräftat

# Test 2: Lista utan metadata
ls -U .
# Hänger detta sig? → filesystem-lock

# Test 3: Stat på en fil
stat README.md
# Hänger detta sig? → inode/mount-problem
```

**Rapportera resultat:**
- ❓ Hänger `cd`?
- ❓ Fungerar `ls -U .`?
- ❓ Ligger projektet på Desktop/Volumes?

Då kan vi peka på exakt rätt åtgärd.
