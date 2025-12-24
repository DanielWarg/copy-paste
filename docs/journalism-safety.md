# Journalism Safety - Källskydd & Etik

Detta dokument beskriver hur Copy/Paste skyddar källor och följer journalistiska etiska principer.

## Översikt

Copy/Paste är designat för att skydda källor och minimera risken för metadata-läckor. Systemet följer strikta principer för källskydd, transparens och mänsklig kontroll.

## Källskydd

### Minimera Metadata

**Princip:** Inget som kan identifiera en källa får hamna i logs eller audit trails.

**Förbjudna fält i logs/audit:**
- IP-adresser (`ip`, `client_ip`, `remote_addr`, `x-forwarded-for`)
- User-Agent (`user_agent`, `user-agent`)
- Referer/Origin (`referer`, `referrer`, `origin`)
- URLs (`url`, `uri`)
- Filnamn (`filename`, `filepath`, `original_filename`)
- Query strings (`querystring`, `query_string`)
- Cookies (`cookies`, `cookie`)
- Headers (`headers`)
- Host information (`host`, `hostname`)

**Beteende:**
- **DEV mode:** Systemet kastar `AssertionError` om förbjudna fält försöker loggas
- **PROD mode:** Systemet droppar fältet tyst och loggar ett säkert warning-event (utan innehåll)

### Source Safety Mode

**Konfiguration:** `SOURCE_SAFETY_MODE=true` (default i produktion)

**HARD MODE:** I produktion (`DEBUG=false`) är `SOURCE_SAFETY_MODE` ALLTID tvingat till `true` och kan inte stängas av.

**Beteende:**
- Om någon försöker sätta `SOURCE_SAFETY_MODE=false` i produktion → Boot fails med `ValueError`
- Systemet tvingar automatiskt `SOURCE_SAFETY_MODE=true` i produktion
- I development (`DEBUG=true`) kan `SOURCE_SAFETY_MODE` stängas av för testning

**Rationale:**
- Källskydd är obligatoriskt för journalistisk användning
- Kan inte kompromissas i produktion
- Fail-fast vid försök att stänga av

**Exempel:**
```bash
# .env (produktion)
DEBUG=false
SOURCE_SAFETY_MODE=true  # Tvingat, kan inte vara false

# Om SOURCE_SAFETY_MODE=false sätts → Boot fails:
# ValueError: SOURCE_SAFETY_MODE cannot be False in production
```

## Transparens

### Process-spårbarhet utan Innehåll

**Princip:** Audit trails visar **vad som hände**, inte **vad som sades**.

**Vad audit visar:**
- Åtgärder (created, updated, exported, deleted)
- Timestamps
- Antal artefakter (counts)
- Format (srt, vtt, quotes)
- Status (ready, archived, destroyed)
- Receipt IDs för destruktion

**Vad audit ALDRIG visar:**
- Transcript-text
- Note-body
- File-content
- Original filnamn (i audit, endast i DB metadata)
- IP-adresser eller annan identifierande metadata

### Audit Event Exempel

**Tillåtet:**
```json
{
  "action": "exported",
  "format": "srt",
  "segments_count": 42,
  "transcript_id": 123
}
```

**Förbjudet:**
```json
{
  "action": "exported",
  "transcript_text": "Detta är förbjudet...",  // ❌ INNEHÅLL
  "client_ip": "192.168.1.1",  // ❌ KÄLLIDENTIFIERARE
  "original_filename": "källa.pdf"  // ❌ FILNAMN
}
```

## Retention & Backups

### Sann Policy

**Princip:** Inget material sparas längre än nödvändigt.

**Beteende:**
- Hard delete: När material raderas, raderas det permanent (med receipt)
- Inga automatiska backups av känsligt material
- Användare måste explicit exportera/arkivera om de vill behålla material

**För känsliga projekt:**
- Filer kan sparas som temp-only (dokumenteras per projekt)
- Överväg automatisk rensning efter X dagar (konfigurerbart)

## Human-in-the-Loop

### Inga Autonoma Beslut

**Princip:** Alla viktiga beslut kräver mänsklig bekräftelse.

**Regler:**
- **Inga autonoma content-förändringar:** Systemet ändrar aldrig innehåll automatiskt
- **Inga "auto-share":** Material delas aldrig automatiskt
- **All export/destroy kräver explicit confirm:** Användare måste bekräfta med `confirm: true` och ange `reason`

### Dry-Run som Default

**Princip:** Farliga operationer körs i dry-run-läge som standard.

**Beteende:**
- `destroy` endpoints: Default `dry_run=true`
- Kräver `{ confirm: true, reason: "..." }` för faktisk destruktion
- Returnerar receipt med `receipt_id`, `destroyed_at`, `counts`

**Exempel:**
```json
// Request
POST /api/v1/projects/123/destroy
{
  "confirm": true,
  "reason": "Projektet är klart och materialet ska raderas enligt policy"
}

// Response
{
  "status": "deleted",
  "receipt_id": "uuid-here",
  "destroyed_at": "2025-12-23T10:00:00",
  "counts": {
    "transcripts": 3,
    "notes": 2,
    "files": 1
  }
}
```

## File Handling

### Original Filnamn

**Princip:** Original filnamn får endast ligga i DB metadata, aldrig i audit/logs.

**Beteende:**
- `original_filename` sparas i `project_files` tabellen (OK för DB metadata)
- Filnamn får ALDRIG hamna i audit events eller logs
- På disk: Filer sparas som `{sha256}.bin` (ingen originalfilnamn)

**För känsliga projekt:**
- Default temp-only för files (dokumenteras per projekt)
- Överväg automatisk rensning efter X dagar

## Ethics Guardrails

### Checklista för Redaktionell Användning

**Före användning:**
- [ ] `SOURCE_SAFETY_MODE=true` är satt i produktion
- [ ] `PROJECT_FILES_KEY` är genererat och säkert lagrat
- [ ] Användare är utbildade i källskydd-principer
- [ ] Retention policy är dokumenterad och förstådd

**Vid användning:**
- [ ] Markera projekt som `sensitive` om materialet är känsligt
- [ ] Använd dry-run för destruktiva operationer
- [ ] Spara receipts för alla destruktiva operationer
- [ ] Verifiera integrity regelbundet (`/api/v1/projects/{id}/verify`)

**Vid export/destroy:**
- [ ] Bekräfta med `confirm: true` och ange `reason`
- [ ] Spara receipt (`receipt_id`) för spårbarhet
- [ ] Verifiera att materialet faktiskt raderades (integrity check)

**Vid fel:**
- [ ] Kontrollera logs för privacy violations (DEV mode)
- [ ] Verifiera att inga källidentifierare läckt (IP, filnamn, etc.)
- [ ] Dokumentera incident och åtgärder

## Tekniska Detaljer

### Log Minimization

**Middleware:**
- Loggar endast: `request_id`, `path` (utan query), `method`, `status_code`, `latency_ms`
- Loggar ALDRIG: `client.host`, `request.headers`, `request.url.query`

**Privacy Guard:**
- Filtrerar automatiskt bort förbjudna fält
- DEV: AssertionError vid överträdelser
- PROD: Droppar fält + loggar safe warning

### Integrity Verification

**Endpoint:** `GET /api/v1/projects/{id}/verify`

**Returnerar:**
```json
{
  "integrity_ok": true,
  "checked": {
    "transcripts": 3,
    "notes": 2,
    "files": 1
  },
  "issues": []
}
```

**Användning:**
- Verifiera att material inte korrupterats
- Kontrollera att filer finns på disk
- Verifiera hash-integrity för notes och transcripts

## Juridiska & Etiska Krav

### Källskydd (Sverige)

- **Tryckfrihetsförordningen:** Skyddar källor och källmaterial
- **Offentlighetsprincipen:** Balans mellan transparens och källskydd
- **GDPR:** Personuppgifter ska minimeras och skyddas

**Copy/Paste följer:**
- Minimering av metadata som kan identifiera källor
- Kryptering av känsligt material
- Möjlighet att permanent radera material (med receipt)

### Etiska Principer

- **Transparens:** Process-spårbarhet utan innehåll
- **Mänsklig kontroll:** Inga autonoma beslut
- **Minimering:** Inget material sparas längre än nödvändigt
- **Källskydd:** Inget som kan identifiera källor i logs/audit

## Secure Delete Policy (Security Statement)

### Vad vi garanterar

**Record Module - File Deletion:**
- ✅ Filer raderas från filsystemet
- ✅ Krypterade blobs tas bort (encrypted content)
- ✅ Best-effort overwrite (kan inte garanteras på SSD)
- ✅ Atomic two-phase destroy (pending → destroyed)
- ✅ Receipt för alla destruktiva handlingar

**Säkerhetsmodell:**
- Vi litar på **encryption-at-rest** + **deletion of encrypted blobs**
- Om filen är krypterad och blobben är raderad: innehållet är säkert även om fysiska bitar finns kvar
- För riktig garanti: Använd disk encryption (LUKS, BitLocker) + kontrollerad storage

### Vad vi INTE garanterar

**Fysisk overwrite:**
- ❌ Kan inte garantera overwrite på SSD (wear leveling, TRIM)
- ❌ Data recovery omöjlighet kräver disk encryption + kontrollerad storage
- ❌ Fysiska bitar kan finnas kvar på SSD även efter radering

**Rationale:**
- SSD använder wear leveling och TRIM - fysisk overwrite är inte möjligt
- Moderna filsystem (ext4, NTFS) garanterar inte fysisk overwrite
- Riktig säkerhet kräver disk encryption på OS-nivå

### Rekommendationer

**För högsta säkerhet:**
1. Använd disk encryption (LUKS, BitLocker) på server-nivå
2. Kontrollerad storage (fysisk säkerhet)
3. Regular key rotation
4. Secure key management (HSM, secrets manager)

**För normal användning:**
- Vår implementation (encryption-at-rest + deletion) är tillräcklig
- Krypterade blobs är säkra även om fysiska bitar finns kvar
- Källskydd skyddas av kryptering, inte fysisk radering

## Support & Frågor

För frågor om källskydd eller etik:
- Kontakta IT-säkerhetsteamet
- Läs `docs/security.md` för tekniska detaljer
- Läs `docs/opsec.md` för operativa säkerhetsrutiner

