# DEL A - Volume Mount Issue med Kolon i Sökvägen

**Problem:** Projektmappen har kolon i namnet: `/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE`

**Symptom:** Docker tolkar kolon (`:`) som volym-separator, vilket gör att volym-mountningar failar.

**Error:**
```
Error response from daemon: invalid volume specification: 
'/host_mnt/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE/Caddyfile.prod_brutal:/etc/caddy/Caddyfile:ro'
```

**Påverkade filer:**
- `docker-compose.prod_brutal.yml` volym-mountningar för:
  - `./Caddyfile.prod_brutal` → proxy container
  - `./certs` → proxy container

**Workarounds:**

### Lösning 1: Flytta Projektet (REKOMMENDERAT)
```bash
mv "/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE" ~/dev/copy_paste
cd ~/dev/copy_paste
```

### Lösning 2: Kopiera Filer in i Container (TILLFÄLLIG)
Använd `docker cp` istället för volym-mountningar, eller bygg in filerna i container-images.

### Lösning 3: Använd Named Volumes
Skapa named volumes och kopiera filer dit via init-container eller script.

**Status:** 
- ✅ Certifikat genererade
- ✅ Backend container kan starta (efter att ca.crt mount kommenterades bort)
- ❌ Proxy container kan inte starta (pga Caddyfile/certs mount)

**Nästa steg:** För att köra full runtime-validering behöver vi antingen:
1. Flytta projektet till sökväg utan kolon
2. Eller implementera workaround för volym-mountningar

