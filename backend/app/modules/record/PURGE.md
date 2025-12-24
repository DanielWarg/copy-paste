# Record Purge (GDPR Retention)

**Modul:** `app.modules.record.purge`

**Ansvar:** Automatisk rensning av utgångna records enligt GDPR retention policy.

---

## Arkitektur

Purge är en **separat modul** (inte CORE, inte API):

- ✅ **Modulär:** Under `app/modules/record/`
- ✅ **CLI-baserad:** Körs explicit (cron, manual, etc)
- ✅ **Idempotent:** Kan köras flera gånger säkert
- ✅ **Privacy-safe:** Loggar endast metadata, aldrig content/paths
- ✅ **Best-effort:** Stoppar aldrig appen vid fel

**Purge exponerar INTE API endpoints** - det är en explicit CLI-operation.

---

## Konfiguration

### Environment Variables

```bash
# Retention period (default: 14 days)
RECORDER_RETENTION_DAYS=14

# Dry-run mode (default: false)
RECORDER_PURGE_DRY_RUN=false
```

### Vad som purgas

Purge rensar allt som är äldre än `RECORDER_RETENTION_DAYS`:

1. **Transcripts** (baserat på `created_at`)
2. **Audio files** (encrypted `.bin` files på disk)
3. **Export ZIPs** (`export-*.zip` i `/app/data`)
4. **DB records** (CASCADE deletes: segments, audit events, audio assets)

---

## Användning

### Via Makefile

```bash
# Dry-run (visar vad som skulle purgas)
make purge-dry-run

# Actual purge
make purge
```

### Via Docker exec

```bash
# Dry-run
docker-compose exec backend python -m app.modules.record.purge_runner --dry-run

# Actual purge
docker-compose exec backend python -m app.modules.record.purge_runner

# Override retention days
docker-compose exec backend python -m app.modules.record.purge_runner --retention-days 7
```

### Via Cron (rekommenderat)

```cron
# Kör purge dagligen kl 02:00
0 2 * * * cd /path/to/project && docker-compose exec -T backend python -m app.modules.record.purge_runner
```

---

## Testning

```bash
# Kör test-skriptet
python scripts/test_purge.py

# Med dry-run
python scripts/test_purge.py --dry-run

# Med custom retention
python scripts/test_purge.py --retention-days 0
```

Test-skriptet:
1. Skapar test record
2. Uploadar audio
3. Exporterar (skapar export ZIP)
4. Destroyar record (skapar orphaned export ZIP)
5. Kör purge (dry-run)
6. Kör purge (actual)
7. Verifierar att export ZIP är borta
8. Kör purge igen (idempotency test)

---

## Logging

Purge loggar endast **privacy-safe metadata**:

```json
{
  "event": "record_purged",
  "transcript_id": 123,
  "age_days": 15,
  "reason": "retention_expired",
  "files_deleted": 1
}
```

**Aldrig loggat:**
- Fil paths
- Content
- User data
- Exception messages (`str(e)`)

---

## Idempotency

Purge är **idempotent** - kan köras flera gånger utan problem:

- Om record redan borta → fortsätt
- Om fil saknas → fortsätt
- Om export ZIP redan borta → fortsätt

**Inga errors** för saknade resurser.

---

## Export ZIP Purge

Export ZIPs (`export-{package_id}.zip`) purgas baserat på **file mtime**:

- **Orphaned exports:** ZIPs för records som destroyats innan purge
- **Expired exports:** ZIPs äldre än retention period

Eftersom `package_id` inte lagras i DB, använder vi file mtime för att identifiera utgångna exports.

---

## GDPR Compliance

Purge säkerställer **dataminimering**:

- ✅ Automatisk rensning efter retention period
- ✅ Rensar allt relaterat material (audio, exports, DB records)
- ✅ Idempotent (säkert att köra flera gånger)
- ✅ Privacy-safe logging (ingen PII leakage)

**När någon frågar "hur säkerställer ni dataminimering?"**
→ Peka på denna modul.

---

## Framtida UI-varning (inte implementerat)

Framtida förbättring: Visa varning i UI när record närmar sig retention:

- "Detta record kommer att raderas automatiskt om X dagar"
- "Kontakta admin för att förlänga retention"

**Status:** Inte implementerat (backend-only för nu).

