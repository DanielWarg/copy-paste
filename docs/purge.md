# Purge Module - Komplett Dokumentation

## Innehållsförteckning

1. [Purpose & Scope](#purpose--scope)
2. [Architecture & Design Principles](#architecture--design-principles)
3. [Configuration](#configuration)
4. [Data Types & Storage](#data-types--storage)
5. [Purge Process](#purge-process)
6. [CLI Interface](#cli-interface)
7. [Execution & Scheduling](#execution--scheduling)
8. [Idempotency & Safety](#idempotency--safety)
9. [Privacy & Logging](#privacy--logging)
10. [Failure Modes & Recovery](#failure-modes--recovery)
11. [GDPR Compliance](#gdpr-compliance)
12. [Testing & Verification](#testing--verification)

---

## Purpose & Scope

Purge-modulen hanterar automatisk rensning av utgångna records enligt GDPR retention policy. Den är designad för att säkerställa dataminimering genom att automatiskt ta bort records som överskridit retention perioden.

### Purpose

**GDPR Compliance:**
- Automatisk dataminimering (Article 5.1.e: "kept in a form which permits identification of data subjects for no longer than is necessary")
- Right to erasure support (Article 17)
- Privacy-by-default implementation

**Operational:**
- Prevent disk space exhaustion
- Maintain database performance
- Clean up orphaned files

### Scope

**In scope:**
- Automatic deletion of expired transcripts (based on `created_at`)
- Deletion of encrypted audio files (`.bin` files on disk)
- Deletion of expired export ZIPs (`export-*.zip` in `/app/data`)
- CASCADE deletion of related DB records (segments, audit events, audio assets)
- CLI-based execution (not API-exposed)
- Idempotent operations (safe to run multiple times)
- Best-effort cleanup (never stops app on error)

**Out of scope:**
- API endpoints (purge is CLI-only)
- Real-time deletion (purge runs on schedule)
- Manual record deletion (handled by destroy endpoint)
- Selective retention (all records use same retention period)

---

## Architecture & Design Principles

### Module Structure

**Location:** `backend/app/modules/record/purge.py`

**Files:**
- `purge.py` - Core purge logic
- `purge_runner.py` - CLI entrypoint
- `PURGE.md` - Quick reference (module-level)

### Design Principles

1. **CLI-only, not API-exposed**
   - Purge is an explicit operation (cron, manual, etc)
   - Never triggered per-request
   - No API endpoints for purge

2. **Idempotent**
   - Can run multiple times safely
   - No errors for missing resources
   - Returns consistent statistics

3. **Best-effort**
   - Never stops app on error
   - Logs errors but continues
   - Returns error count in statistics

4. **Privacy-safe**
   - No filenames, paths, or content in logs
   - Only metadata (IDs, counts, timestamps)
   - No PII leakage

5. **Explicit execution**
   - Requires manual trigger (cron, CLI)
   - Dry-run default (configurable)
   - Clear logging of what would be deleted

### Relationship to Record Module

**Purge is part of Record module:**
- Location: `app/modules/record/purge.py`
- Responsibility: Lifecycle management for Record data
- Not CORE functionality (modular, optional)

**Purge vs Destroy:**
- **Destroy:** Manual, API-based, single record, user-initiated
- **Purge:** Automatic, CLI-based, batch operation, schedule-initiated

---

## Configuration

### Environment Variables

**Retention Period:**
```bash
# Retention period in days (default: 14)
RECORDER_RETENTION_DAYS=14
```

**Dry-run Mode:**
```bash
# Dry-run mode (default: false)
# If true, only logs what would be purged, doesn't delete
RECORDER_PURGE_DRY_RUN=false
```

### Configuration Loading

**Source:** `app.core.config.Settings`

**Loading order:**
1. Environment variables (`.env` file or system env)
2. Default values (14 days retention, false dry-run)
3. CLI arguments override (if provided)

**Validation:**
- Retention days must be positive integer
- Dry-run is boolean
- Config loaded at import time (fail-fast on invalid config)

---

## Data Types & Storage

### What Gets Purged

Purge rensar allt som är äldre än `RECORDER_RETENTION_DAYS`:

1. **Transcripts** (primary target)
   - Based on `Transcript.created_at < cutoff_date`
   - Deleted via `db.delete(transcript)`
   - CASCADE deletes related records

2. **Audio Files** (encrypted `.bin` files)
   - Location: `/app/data/files/{sha256}.bin`
   - Deleted via `delete_file(sha256)`
   - Best-effort (continues if file already deleted)

3. **Export ZIPs** (`export-*.zip` files)
   - Location: `/app/data/export-{package_id}.zip`
   - Deleted based on file mtime (modification time)
   - Covers orphaned exports (records destroyed before purge)

4. **Related DB Records** (CASCADE deletes)
   - `TranscriptSegment` (segments)
   - `TranscriptAuditEvent` (audit events)
   - `AudioAsset` (audio asset records)

### Retention Timestamp

**Primary timestamp:** `Transcript.created_at`

**Rationale:**
- Transcript creation is the "birth" of the record
- All related data (audio, segments, audit) is tied to transcript
- Consistent retention calculation

**Cutoff calculation:**
```python
cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
```

### Export ZIP Retention

**Challenge:** `package_id` not stored in DB, so we can't link ZIPs to transcripts

**Solution:** Purge based on file mtime (modification time)

**Behavior:**
- Find all `export-*.zip` files in `/app/data`
- Check file mtime against cutoff date
- Delete if `mtime < cutoff_date`

**Covers:**
- Export ZIPs for purged records (orphaned after record deletion)
- Export ZIPs for records that were destroyed before purge
- Export ZIPs that exceed retention period

**Limitation:**
- Cannot distinguish between valid and orphaned exports
- Relies on file mtime (may be inaccurate if file system time is wrong)

---

## Purge Process

### Process Flow

**1. Initialization:**
```python
# Load configuration
dry_run = settings.recorder_purge_dry_run
retention_days = settings.recorder_retention_days
cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

# Initialize statistics
stats = {
    "purged_count": 0,
    "files_deleted": 0,
    "exports_deleted": 0,
    "errors": 0,
    "dry_run": dry_run,
    "retention_days": retention_days,
    "cutoff_date": cutoff_date.isoformat(),
}
```

**2. Database Check:**
- If `DATABASE_URL` not set → skip purge, return stats
- If DB unavailable → log error, return stats with `errors=1`

**3. Find Expired Transcripts:**
```python
expired_transcripts = db.query(Transcript).filter(
    Transcript.created_at < cutoff_date
).all()
```

**4. Process Each Transcript:**
```python
for transcript in expired_transcripts:
    # Get audio assets
    audio_assets = db.query(AudioAsset).filter(
        AudioAsset.transcript_id == transcript.id
    ).all()
    
    # Collect sha256 values for file deletion
    sha256_values = [a.sha256 for a in audio_assets]
    
    if dry_run:
        # Log what would be purged
        logger.info("record_purge_candidate", ...)
    else:
        # Delete audio files from disk (best-effort)
        for sha256 in sha256_values:
            try:
                delete_file(sha256)
                stats["files_deleted"] += 1
            except Exception:
                stats["errors"] += 1
        
        # Delete transcript (CASCADE deletes related records)
        db.delete(transcript)
        db.commit()
        
        stats["purged_count"] += 1
```

**5. Purge Orphaned Export ZIPs:**
```python
# Find export-*.zip files
export_files = list(Path("/app/data").glob("export-*.zip"))

for zip_path in export_files:
    mtime = datetime.fromtimestamp(zip_path.stat().st_mtime)
    if mtime < cutoff_date:
        if dry_run:
            logger.info("export_purge_candidate", ...)
        else:
            zip_path.unlink()
            stats["exports_deleted"] += 1
```

**6. Return Statistics:**
```python
return {
    "purged_count": stats["purged_count"],
    "files_deleted": stats["files_deleted"],
    "exports_deleted": stats["exports_deleted"],
    "errors": stats["errors"],
    "dry_run": dry_run,
    "retention_days": retention_days,
    "cutoff_date": cutoff_date.isoformat(),
}
```

### Transaction Handling

**Per-transcript transaction:**
- Each transcript deletion is wrapped in try/except
- On error: rollback transaction, log error, continue with next
- On success: commit transaction, log purge, continue with next

**Rationale:**
- Prevents one failed deletion from stopping entire purge
- Best-effort cleanup (partial success is better than total failure)

### CASCADE Deletes

**When transcript is deleted:**
- SQLAlchemy CASCADE deletes related records:
  - `TranscriptSegment` (segments)
  - `TranscriptAuditEvent` (audit events)
  - `AudioAsset` (audio asset records)

**Implication:**
- No need to manually delete related records
- Atomic operation (all-or-nothing per transcript)

---

## CLI Interface

### Entry Point

**Command:** `python -m app.modules.record.purge_runner [OPTIONS]`

**Usage:**
```bash
# Dry-run (shows what would be purged)
python -m app.modules.record.purge_runner --dry-run

# Actual purge
python -m app.modules.record.purge_runner

# Override retention days
python -m app.modules.record.purge_runner --retention-days 7

# Dry-run with custom retention
python -m app.modules.record.purge_runner --dry-run --retention-days 30
```

### Arguments

**`--dry-run`** (optional, flag)
- If set: only log what would be purged, don't delete
- Default: uses `RECORDER_PURGE_DRY_RUN` env var

**`--retention-days N`** (optional, integer)
- Override retention days (default: `RECORDER_RETENTION_DAYS` env var)
- Must be positive integer

### Output

**Stdout (for cron logs):**
```
Purge complete:
  Dry run: false
  Retention days: 14
  Purged records: 5
  Files deleted: 5
  Exports deleted: 3
  Errors: 0
```

**Stderr (on error):**
```
Error: ValueError
```

**Logs (structured JSON):**
```json
{
  "event": "purge_run_started",
  "dry_run": false,
  "retention_days": 14
}
```

### Exit Codes

- **0:** Success (no errors)
- **1:** Errors occurred (but purge completed)
- **130:** Interrupted (SIGINT)

**Note:** Exit code 1 doesn't mean purge failed - it means some errors occurred during cleanup. Check error count in statistics.

---

## Execution & Scheduling

### Manual Execution

**Via Makefile:**
```bash
# Dry-run
make purge-dry-run

# Actual purge
make purge
```

**Via Docker exec:**
```bash
# Dry-run
docker-compose exec backend python -m app.modules.record.purge_runner --dry-run

# Actual purge
docker-compose exec backend python -m app.modules.record.purge_runner

# Override retention days
docker-compose exec backend python -m app.modules.record.purge_runner --retention-days 7
```

### Scheduled Execution (Cron)

**Daily purge (recommended):**
```cron
# Run purge daily at 02:00
0 2 * * * cd /path/to/project && docker-compose exec -T backend python -m app.modules.record.purge_runner
```

**Weekly purge (alternative):**
```cron
# Run purge weekly on Sunday at 03:00
0 3 * * 0 cd /path/to/project && docker-compose exec -T backend python -m app.modules.record.purge_runner
```

**With logging:**
```cron
# Run purge daily and log to file
0 2 * * * cd /path/to/project && docker-compose exec -T backend python -m app.modules.record.purge_runner >> /var/log/purge.log 2>&1
```

### Execution Best Practices

1. **Schedule during low-traffic hours** (e.g., 02:00-04:00)
2. **Monitor first few runs** (check logs, verify deletions)
3. **Start with dry-run** (verify what would be purged)
4. **Set up alerts** (monitor error count in statistics)
5. **Document retention policy** (make retention period clear to users)

---

## Idempotency & Safety

### Idempotent Operations

**Purge is idempotent:** Can run multiple times safely

**Behavior:**
- If transcript already deleted → continues without error
- If file already deleted → continues without error
- If export ZIP already deleted → continues without error
- Returns consistent statistics (0 purged if nothing to purge)

**Rationale:**
- Safe to run multiple times
- Safe to run after manual deletions
- Safe to run after failed purges

### Safety Guarantees

**Never stops app:**
- All exceptions caught and logged
- Never raises unhandled exceptions
- Returns statistics even on critical failures

**Best-effort cleanup:**
- Continues on individual record failures
- Logs errors but doesn't stop
- Returns error count in statistics

**Dry-run default:**
- `RECORDER_PURGE_DRY_RUN=true` by default (configurable)
- Shows what would be purged without deleting
- Safe to test before actual purge

### Error Handling

**Per-record errors:**
- Try/except around each transcript deletion
- On error: rollback transaction, log error, continue
- Error count incremented in statistics

**Export ZIP errors:**
- Try/except around ZIP deletion
- On error: log error, continue with next file
- Error count incremented in statistics

**Critical errors:**
- Try/except around entire purge function
- On error: log error, return statistics with `errors=1`
- Never raises unhandled exceptions

---

## Privacy & Logging

### Privacy-Safe Logging

**What is logged:**
```json
{
  "event": "record_purged",
  "transcript_id": 123,
  "age_days": 15,
  "reason": "retention_expired",
  "files_deleted": 1
}
```

**What is NOT logged:**
- ❌ Filenames
- ❌ File paths
- ❌ File content
- ❌ User data
- ❌ Exception messages (`str(e)`)
- ❌ Request payloads

### Log Events

**Purge start:**
```json
{
  "event": "purge_run_started",
  "dry_run": false,
  "retention_days": 14
}
```

**Purge candidate (dry-run):**
```json
{
  "event": "record_purge_candidate",
  "transcript_id": 123,
  "age_days": 15,
  "audio_files_count": 1,
  "reason": "retention_expired"
}
```

**Purge completed:**
```json
{
  "event": "record_purged",
  "transcript_id": 123,
  "age_days": 15,
  "reason": "retention_expired",
  "files_deleted": 1
}
```

**Export purge candidate:**
```json
{
  "event": "export_purge_candidate",
  "file_age_days": 15,
  "reason": "retention_expired"
}
```

**Export purge completed:**
```json
{
  "event": "export_orphan_purged",
  "file_age_days": 15,
  "reason": "retention_expired"
}
```

**Purge complete:**
```json
{
  "event": "record_purge_complete",
  "purged_count": 5,
  "files_deleted": 5,
  "exports_deleted": 3,
  "errors": 0,
  "dry_run": false
}
```

**Purge errors:**
```json
{
  "event": "record_purge_failed",
  "transcript_id": 123,
  "error_type": "ValueError"
}
```

### Logging Standards

**Follows CORE logging standards:**
- Structured JSON logging
- Privacy-safe (no PII)
- Consistent event names
- Request ID correlation (if available)

**Error logging:**
- Log error type (`type(e).__name__`)
- Never log error message (`str(e)`) - may contain sensitive data
- Include context (transcript_id, error_type)

---

## Failure Modes & Recovery

### Failure Scenarios

**1. Database Unavailable:**
- **Behavior:** Logs error, returns stats with `errors=1`
- **Recovery:** Retry when DB is available
- **Impact:** No records purged, but purge can be rerun

**2. Individual Record Deletion Fails:**
- **Behavior:** Logs error, rollbacks transaction, continues with next
- **Recovery:** Purge can be rerun (idempotent)
- **Impact:** Failed record remains, others are purged

**3. File Deletion Fails:**
- **Behavior:** Logs error, increments error count, continues
- **Recovery:** File remains on disk (orphaned)
- **Impact:** File can be manually deleted or purged in next run

**4. Export ZIP Deletion Fails:**
- **Behavior:** Logs error, increments error count, continues
- **Recovery:** ZIP remains on disk (orphaned)
- **Impact:** ZIP can be manually deleted or purged in next run

**5. Critical Error (unhandled exception):**
- **Behavior:** Logs error, returns stats with `errors=1`
- **Recovery:** Purge can be rerun (idempotent)
- **Impact:** Partial purge may have occurred

### Recovery Procedures

**After purge with errors:**
1. Check error count in statistics
2. Review logs for error types
3. Fix underlying issues (DB connectivity, file permissions)
4. Rerun purge (idempotent, safe to rerun)

**After partial purge:**
1. Purge is idempotent - safe to rerun
2. Next purge will process remaining records
3. No duplicate deletions (CASCADE deletes prevent)

**Orphaned files:**
1. Files may remain if deletion fails
2. Next purge will attempt deletion again
3. Manual cleanup possible (but not recommended)

### Data Consistency

**Guarantees:**
- Transcript deletion is atomic (CASCADE deletes related records)
- File deletion is best-effort (may leave orphaned files)
- Export ZIP deletion is best-effort (may leave orphaned ZIPs)

**Inconsistencies:**
- Orphaned files (if file deletion fails)
- Orphaned export ZIPs (if ZIP deletion fails)
- Partial purge (if critical error occurs)

**Mitigation:**
- Idempotent purge (safe to rerun)
- Best-effort cleanup (continues on errors)
- Error logging (identify and fix issues)

---

## GDPR Compliance

### Data Minimization (Article 5.1.e)

**Automatic retention:**
- Records purged after `RECORDER_RETENTION_DAYS` (default: 14)
- All related data deleted (audio, transcripts, segments, audit, exports)
- Prevents indefinite storage of personal data

### Right to Erasure (Article 17)

**Manual destruction:**
- Users can destroy records via API (`POST /api/v1/record/{id}/destroy`)
- Requires confirmation and reason (audit trail)

**Automatic purge:**
- Records purged after retention period
- All related data deleted (including orphaned export ZIPs)
- No manual intervention required

### Privacy-by-Default (Article 25)

**Privacy-safe logging:**
- No filenames, paths, or content in logs
- Only metadata (IDs, counts, timestamps)
- No PII leakage

**Configuration:**
- Retention period configurable via env var
- Dry-run default (configurable)
- Explicit execution (cron, manual)

### Audit Trail

**Purge audit events:**
- `purge_run_started` - Purge execution started
- `record_purge_candidate` - Record identified for purge (dry-run)
- `record_purged` - Record purged (actual)
- `export_purge_candidate` - Export ZIP identified for purge (dry-run)
- `export_orphan_purged` - Export ZIP purged (actual)
- `record_purge_complete` - Purge execution completed

**Audit privacy:**
- No content, no filenames, no paths
- Only metadata (action, timestamp, counts)
- Error types logged (not error messages)

---

## Testing & Verification

### Manual Testing

**Test script:** `scripts/test_purge.py`

**Test flow:**
1. Create test record
2. Upload audio
3. Export (creates export ZIP)
4. Destroy record (creates orphaned export ZIP)
5. Run purge (dry-run) - verify what would be purged
6. Run purge (actual) - verify deletions
7. Verify export ZIP is deleted
8. Run purge again (idempotency test) - verify no duplicates

**Usage:**
```bash
# Run test script
python scripts/test_purge.py

# With dry-run
python scripts/test_purge.py --dry-run

# With custom retention (0 = immediate)
python scripts/test_purge.py --retention-days 0
```

### Verification Checklist

**After purge:**
- ✅ Expired transcripts deleted from DB
- ✅ Encrypted audio files deleted from disk
- ✅ Expired export ZIPs deleted from disk
- ✅ Related DB records deleted (CASCADE)
- ✅ Statistics match expected counts
- ✅ No errors in logs (or errors logged appropriately)
- ✅ Idempotency verified (rerun produces same results)

### Production Monitoring

**Key metrics:**
- Purge execution time
- Records purged per run
- Files deleted per run
- Export ZIPs deleted per run
- Error count per run

**Alerts:**
- High error count (>10% of records)
- Purge execution failure (exit code 1)
- Unexpected purge counts (too many/too few)

**Log analysis:**
- Review purge logs daily
- Check for consistent error patterns
- Verify retention policy compliance

---

## Summary

Purge-modulen tillhandahåller GDPR-compliant automatisk rensning av utgångna records med:

- **CLI-only execution:** Explicit operation (cron, manual), not API-exposed
- **Idempotent operations:** Safe to run multiple times
- **Best-effort cleanup:** Never stops app on error
- **Privacy-safe logging:** No PII in logs
- **Comprehensive deletion:** Records, files, exports, related DB data
- **Configurable retention:** Environment variable configuration
- **GDPR compliance:** Data minimization, right to erasure, privacy-by-default

**När någon frågar "hur säkerställer ni dataminimering?"**
→ Peka på Purge-modulens automatiska retention och best-effort cleanup.

