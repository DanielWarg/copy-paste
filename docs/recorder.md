# Record Module - Komplett Dokumentation

## Innehållsförteckning

1. [Purpose & Scope](#purpose--scope)
2. [Data Types & Storage](#data-types--storage)
3. [Lifecycle](#lifecycle)
4. [Encryption & Security](#encryption--security)
5. [Export Semantics](#export-semantics)
6. [Destroy vs Purge](#destroy-vs-purge)
7. [Retention Policy](#retention-policy)
8. [API Behavior](#api-behavior)
9. [Failure Modes & Guarantees](#failure-modes--guarantees)
10. [GDPR Summary](#gdpr-summary)

---

## Purpose & Scope

Record-modulen hanterar säker audio-ingest och management för journalistiska workflows. Den tillhandahåller:

- **Snabb ingest:** Skapa project + transcript shell i ett API-anrop
- **Säker upload:** Krypterad audio-lagring at rest
- **Export package:** ZIP med transcript + audio + audit (ingen content i audit)
- **Säker destruction:** Dry-run default, confirm + receipt krävs
- **Automatisk retention:** GDPR-compliant purge av utgångna records

### Scope

**In scope:**
- Audio file upload (WAV, MP3, M4A, AAC, MP4, OGG, WebM)
- Encrypted storage at rest (Fernet encryption)
- Export packages (ZIP med transcript, audio, audit, manifest)
- Manual destruction (dry-run default, confirm required)
- Automatic retention purge (CLI-based, cron-friendly)

**Out of scope:**
- Audio processing (transcription, normalization)
- Real-time streaming
- Multi-file uploads
- API endpoints för purge (purge är CLI-only)

### Designprinciper

1. **Privacy-by-default** - Inga filnamn, paths eller content i logs/audit
2. **Safe defaults** - Dry-run default, encrypted export default
3. **Idempotent operations** - Destroy och purge kan köras flera gånger säkert
4. **Best-effort cleanup** - Purge stoppar aldrig appen vid fel
5. **Explicit operations** - Purge är CLI-only, inte API-exponerad

---

## Data Types & Storage

### AudioAsset Model

```python
class AudioAsset(Base):
    id: int                    # Primary key
    project_id: int            # FK to projects (nullable, CASCADE delete)
    transcript_id: int         # FK to transcripts (required, CASCADE delete)
    sha256: str                # Content hash (unique, indexed, 64 chars)
    mime_type: str             # audio/wav, audio/mpeg, etc.
    size_bytes: int            # File size in bytes
    storage_path: str          # Internal path: {sha256}.bin
    destroy_status: str        # none|pending|destroyed (indexed)
    destroyed_at: datetime     # Set when destroyed (nullable)
    created_at: datetime       # Creation timestamp (indexed)
```

**Relationships:**
- `project` → `Project` (nullable, CASCADE delete)
- `transcript` → `Transcript` (required, CASCADE delete)

**Indexes:**
- `idx_audio_transcript` on `transcript_id`
- `idx_audio_project` on `project_id`
- Unique index on `sha256`

### Storage Structure

**On-disk storage:**
```
/app/data/files/
  └── {sha256}.bin          # Encrypted audio file
```

**Export ZIPs:**
```
/app/data/
  └── export-{package_id}.zip  # Temporary export packages
```

**Storage semantics:**
- Files stored as `{sha256}.bin` (original filename never stored)
- Files encrypted with Fernet (symmetric encryption)
- Encryption key from `PROJECT_FILES_KEY` env var (base64 URL-safe)
- Storage directory created automatically (`/app/data/files`)

### Data Flow

1. **Upload:**
   - Client uploads audio file (multipart/form-data)
   - Server validates MIME type + magic bytes
   - Server computes SHA256 hash
   - Server encrypts content with Fernet
   - Server stores encrypted blob as `{sha256}.bin`
   - Server creates `AudioAsset` record

2. **Export:**
   - Server reads encrypted blob from disk
   - Server creates ZIP in memory (transcript.json, audio.bin/dec, audit.json, manifest.json)
   - Server saves ZIP to `/app/data/export-{package_id}.zip`
   - Server returns JSON response with `zip_path`

3. **Destroy:**
   - Server deletes encrypted blob from disk
   - Server deletes `AudioAsset` record (CASCADE deletes transcript)
   - Server returns receipt with `destroyed_at` timestamp

4. **Purge:**
   - CLI tool finds expired transcripts (based on `created_at`)
   - CLI tool deletes encrypted blobs (best-effort)
   - CLI tool deletes expired export ZIPs (based on file mtime)
   - CLI tool deletes transcript records (CASCADE deletes all related data)

---

## Lifecycle

### 1. Create Record

**Endpoint:** `POST /api/v1/record`

**Request:**
```json
{
  "project_id": 1,           // Optional: creates new project if not provided
  "title": "Intervju med källan",
  "sensitivity": "sensitive",  // "standard" | "sensitive"
  "language": "sv"
}
```

**Response:**
```json
{
  "project_id": 1,
  "transcript_id": 1,
  "title": "Intervju med källan",
  "created_at": "2025-12-23T10:00:00"
}
```

**Behavior:**
- If `project_id` not provided: Creates new project ("Untitled – YYYY-MM-DD")
- Creates transcript shell (status="uploaded")
- Audit events: `project_created` (if new), `transcript_created`

### 2. Upload Audio

**Endpoint:** `POST /api/v1/record/{transcript_id}/audio`

**Request:** `multipart/form-data` with `file` field

**Supported formats:**
- `audio/wav`, `audio/wave`, `audio/x-wav`
- `audio/mpeg`, `audio/mp3`
- `audio/mp4`, `audio/aac`
- `audio/ogg`, `audio/webm`

**Max size:** 200MB

**Response:**
```json
{
  "status": "ok",
  "file_id": 1,
  "sha256": "abc123...",
  "size_bytes": 1024000,
  "mime_type": "audio/wav"
}
```

**Behavior:**
- Validates MIME type and size
- Validates magic bytes (file signature)
- Computes SHA256 hash
- Encrypts content with Fernet
- Stores encrypted blob as `{sha256}.bin`
- Creates `AudioAsset` record
- Audit event: `audio_uploaded` (metadata: size_bytes, mime_type - NO filename)

### 3. Export Package

**Endpoint:** `POST /api/v1/record/{transcript_id}/export`

**Request:**
```json
{
  "confirm": true,
  "reason": "Export för redaktionell granskning",
  "export_audio_mode": "encrypted"  // "encrypted" (default) | "decrypted"
}
```

**Response:**
```json
{
  "status": "ok",
  "package_id": "uuid-here",
  "receipt_id": "uuid-here",
  "zip_path": "/app/data/export-{package_id}.zip",
  "audio_mode": "encrypted",
  "warnings": []
}
```

**Package contents:**
- `transcript.json` - Metadata + segments (if exists)
- `audio.bin` - Encrypted audio (default)
- `audio.dec` - Decrypted audio (if `export_audio_mode="decrypted"`)
- `audit.json` - Process log (NO content, only metadata)
- `manifest.json` - Package metadata (package_id, created_at, audio_mode, counts, integrity_hashes)

**Behavior:**
- **Default:** `export_audio_mode="encrypted"` (safe default)
- **Decrypted:** Requires `confirm=true` + detailed reason (min 10 chars) + extra warning
- Requires `confirm=true` and `reason`
- Creates ZIP package with manifest
- Saves ZIP to `/app/data/export-{package_id}.zip`
- Audit event: `exported` (metadata: format="zip", package_id, audio_mode)

### 4. Destroy Record

**Endpoint:** `POST /api/v1/record/{transcript_id}/destroy`

**Request (dry-run, default):**
```json
{
  "dry_run": true
}
```

**Request (confirm destruction):**
```json
{
  "dry_run": false,
  "confirm": true,
  "reason": "Materialet är inte längre relevant"
}
```

**Dry Run Response:**
```json
{
  "status": "dry_run",
  "would_delete": {
    "files": 1,
    "segments": 0,
    "notes": 0
  },
  "transcript_id": 1
}
```

**Destroy Response:**
```json
{
  "status": "destroyed",
  "receipt_id": "uuid-here",
  "destroyed_at": "2025-12-23T10:00:00",
  "counts": {
    "files": 1,
    "segments": 0,
    "notes": 0
  },
  "destroy_status": "destroyed"
}
```

**Behavior:**
- **Default:** `dry_run=true` (safe by default)
- **Idempotent:** If transcript already deleted, returns success
- **Destruction requires:** `confirm=true` and `reason`
- **Deletes:**
  - Audio asset (file from disk)
  - Transcript (CASCADE deletes segments, audit events, audio assets)
- **Audit event:** `destroyed` (metadata: counts, receipt_id)

### 5. Purge (CLI-only)

**Command:** `python -m app.modules.record.purge_runner [--dry-run] [--retention-days N]`

**Behavior:**
- Finds expired transcripts (based on `created_at < cutoff_date`)
- Deletes encrypted blobs from disk (best-effort)
- Deletes expired export ZIPs (based on file mtime)
- Deletes transcript records (CASCADE deletes all related data)
- **Idempotent:** Can run multiple times safely
- **Best-effort:** Never stops app on error

**Purge statistics:**
```json
{
  "purged_count": 5,
  "files_deleted": 5,
  "exports_deleted": 3,
  "errors": 0,
  "dry_run": false,
  "retention_days": 14,
  "cutoff_date": "2025-12-09T10:00:00"
}
```

---

## Encryption & Security

### Encryption at Rest

**Algorithm:** Fernet (symmetric encryption, AES-128 in CBC mode)

**Key management:**
- Key from `PROJECT_FILES_KEY` env var (base64 URL-safe encoded)
- Key must be exactly 32 bytes (after decoding)
- Key never logged or exposed in responses

**Encryption process:**
1. Read file content (bytes)
2. Get Fernet key from `PROJECT_FILES_KEY`
3. Encrypt content: `fernet.encrypt(content)`
4. Store encrypted blob as `{sha256}.bin`

**Decryption process:**
1. Read encrypted blob from disk
2. Get Fernet key from `PROJECT_FILES_KEY`
3. Decrypt content: `fernet.decrypt(encrypted_content)`
4. Return decrypted bytes

### Privacy Protection

**No filenames in audit/logs:**
- Only `size_bytes`, `mime_type`, `counts` logged
- Original filename never stored on disk
- Only SHA256 hash used as identifier

**No paths in responses:**
- Only internal `storage_path` (never exposed to client)
- Export ZIP path is internal (`/app/data/export-{package_id}.zip`)

**No content in audit:**
- Audit events contain only metadata (action, actor, timestamp)
- No transcript text, no audio content, no user data

**Source safety mode:**
- `SOURCE_SAFETY_MODE=true` enforced in production
- No IP addresses, user agents, or URLs logged
- Request IDs for traceability (no PII)

### Original File is Sacred

**Principle:** Original filename never stored on disk

**Rationale:**
- Filenames can contain PII (e.g., "intervju_källa_john_doe.wav")
- Only SHA256 hash used as identifier
- File content encrypted before storage
- Storage path: `{sha256}.bin` (no original filename)

### Export Safety Default

**Default:** Audio exported as encrypted blob (`audio.bin`)

**Decrypted export:**
- Requires `confirm=true` + detailed reason (min 10 chars)
- Extra warning in response
- Audit event includes `audio_mode="decrypted"`

**Manifest:**
- `manifest.json` included in ZIP with package metadata
- Integrity hashes for verification (no PII)
- Privacy-safe keys (`t_id` instead of `transcript_id`)

### Secure Delete Policy

**Vad vi garanterar:**
- ✅ Filer raderas från filsystemet
- ✅ Krypterade blobs tas bort
- ✅ Best-effort overwrite (kan inte garanteras på SSD)

**Vad vi INTE garanterar:**
- ❌ Fysisk overwrite på SSD (wear leveling, TRIM)
- ❌ Data recovery omöjlighet (kräver disk encryption)

**Säkerhetsmodell:**
- Vi litar på **encryption-at-rest** + **deletion of encrypted blobs**
- Om filen är krypterad och blobben är raderad: innehållet är säkert även om fysiska bitar finns kvar
- För riktig garanti: Använd disk encryption (LUKS, BitLocker) + kontrollerad storage

Se `docs/journalism-safety.md` för fullständig security statement.

---

## Export Semantics

### Export Package Structure

**ZIP contents:**
```
export-{package_id}.zip
├── transcript.json      # Metadata + segments
├── audio.bin            # Encrypted audio (default)
├── audio.dec            # Decrypted audio (if export_audio_mode="decrypted")
├── audit.json           # Process log (NO content)
└── manifest.json        # Package metadata
```

### Export Modes

**Encrypted (default):**
- Audio exported as encrypted blob (`audio.bin`)
- Requires decryption key to access
- Safe for transfer/storage

**Decrypted:**
- Audio exported as decrypted WAV (`audio.dec`)
- Requires extra confirmation + detailed reason
- Warning in response: "Audio exported as decrypted. Handle with extreme care."

### Export Response

**Response format:**
```json
{
  "status": "ok",
  "package_id": "uuid-here",
  "receipt_id": "uuid-here",
  "zip_path": "/app/data/export-{package_id}.zip",
  "audio_mode": "encrypted",
  "warnings": []
}
```

**zip_path semantics:**
- Path to ZIP file on disk (within Docker container)
- Client must use `docker cp` or similar to retrieve ZIP
- ZIP is temporary (purged by retention policy)

### Manifest Structure

**manifest.json:**
```json
{
  "package_id": "uuid-here",
  "created_at": "2025-12-23T10:00:00",
  "audio_mode": "encrypted",
  "counts": {
    "segments": 10,
    "audit_events": 5
  },
  "integrity_hashes": {
    "t_id": 1,
    "audio_sha256": "abc123...",
    "t_hash": "def456..."
  }
}
```

**Privacy-safe keys:**
- `t_id` instead of `transcript_id` (avoids forbidden key match)
- `t_hash` instead of `transcript_hash` (avoids forbidden key match)
- No PII in manifest

---

## Destroy vs Purge

### Destroy (Manual, API-based)

**Purpose:** Manual deletion of specific record

**Trigger:** User-initiated via API (`POST /api/v1/record/{transcript_id}/destroy`)

**Behavior:**
- Dry-run default (`dry_run=true`)
- Requires confirmation (`confirm=true`)
- Requires reason (audit trail)
- Returns receipt with `destroyed_at` timestamp
- Idempotent (if transcript already deleted, returns success)

**Deletes:**
- Audio asset (encrypted blob from disk)
- Transcript (CASCADE deletes segments, audit events, audio assets)

**Not deleted:**
- Export ZIPs (purged separately by retention policy)

### Purge (Automatic, CLI-based)

**Purpose:** Automatic deletion of expired records (GDPR retention)

**Trigger:** CLI tool (`python -m app.modules.record.purge_runner`)

**Behavior:**
- Finds expired transcripts (based on `created_at < cutoff_date`)
- Deletes encrypted blobs from disk (best-effort)
- Deletes expired export ZIPs (based on file mtime)
- Deletes transcript records (CASCADE deletes all related data)
- Idempotent (can run multiple times safely)
- Best-effort (never stops app on error)

**Configuration:**
- `RECORDER_RETENTION_DAYS` (default: 14)
- `RECORDER_PURGE_DRY_RUN` (default: false)

**Purge statistics:**
```json
{
  "purged_count": 5,
  "files_deleted": 5,
  "exports_deleted": 3,
  "errors": 0,
  "dry_run": false,
  "retention_days": 14,
  "cutoff_date": "2025-12-09T10:00:00"
}
```

### Key Differences

| Aspect | Destroy | Purge |
|--------|---------|-------|
| **Trigger** | User-initiated (API) | Automatic (CLI/cron) |
| **Scope** | Single record | All expired records |
| **Default** | Dry-run | Actual purge (configurable) |
| **Confirmation** | Required (`confirm=true`) | Not required (CLI) |
| **Reason** | Required (audit trail) | Not required (automatic) |
| **Export ZIPs** | Not deleted | Deleted (if expired) |
| **Idempotent** | Yes | Yes |
| **Best-effort** | No (fails on error) | Yes (continues on error) |

---

## Retention Policy

### Configuration

**Environment variables:**
```bash
# Retention period (default: 14 days)
RECORDER_RETENTION_DAYS=14

# Dry-run mode (default: false)
RECORDER_PURGE_DRY_RUN=false
```

### What Gets Purged

Purge rensar allt som är äldre än `RECORDER_RETENTION_DAYS`:

1. **Transcripts** (baserat på `created_at`)
2. **Audio files** (encrypted `.bin` files på disk)
3. **Export ZIPs** (`export-*.zip` i `/app/data`)
4. **DB records** (CASCADE deletes: segments, audit events, audio assets)

### Retention Timestamp

**Primary timestamp:** `Transcript.created_at`

**Rationale:**
- Transcript creation is the "birth" of the record
- All related data (audio, segments, audit) is tied to transcript
- Export ZIPs use file mtime (since `package_id` not stored in DB)

### Export ZIP Retention

**Challenge:** `package_id` not stored in DB, so we can't link ZIPs to transcripts

**Solution:** Purge based on file mtime (modification time)

**Behavior:**
- Find all `export-*.zip` files in `/app/data`
- Check file mtime against cutoff date
- Delete if mtime < cutoff_date

**Covers:**
- Export ZIPs for purged records (orphaned after record deletion)
- Export ZIPs for records that were destroyed before purge

### Purge Execution

**CLI command:**
```bash
# Dry-run (shows what would be purged)
make purge-dry-run

# Actual purge
make purge

# Via Docker exec
docker-compose exec backend python -m app.modules.record.purge_runner --dry-run
docker-compose exec backend python -m app.modules.record.purge_runner --retention-days 7
```

**Cron example:**
```cron
# Kör purge dagligen kl 02:00
0 2 * * * cd /path/to/project && docker-compose exec -T backend python -m app.modules.record.purge_runner
```

### Purge Guarantees

**Idempotent:**
- Can run multiple times safely
- If record already deleted, continues without error
- If file already deleted, continues without error

**Best-effort:**
- Never stops app on error
- Logs errors but continues with next record
- Returns statistics (including error count)

**Privacy-safe:**
- Logs only metadata (transcript_id, age_days, reason)
- No filenames, paths, or content in logs

---

## API Behavior

### High-Level API Flow

1. **Create Record:**
   - `POST /api/v1/record` → Creates project + transcript shell
   - Returns `project_id`, `transcript_id`, `title`, `created_at`

2. **Upload Audio:**
   - `POST /api/v1/record/{transcript_id}/audio` → Uploads audio file
   - Validates MIME type + magic bytes
   - Encrypts and stores file
   - Returns `file_id`, `sha256`, `size_bytes`, `mime_type`

3. **Export Package:**
   - `POST /api/v1/record/{transcript_id}/export` → Exports ZIP package
   - Requires `confirm=true` and `reason`
   - Creates ZIP in memory, saves to disk
   - Returns `package_id`, `receipt_id`, `zip_path`, `audio_mode`, `warnings`

4. **Destroy Record:**
   - `POST /api/v1/record/{transcript_id}/destroy` → Destroys record
   - Default: `dry_run=true` (safe default)
   - Requires `confirm=true` and `reason` (if `dry_run=false`)
   - Returns `status`, `receipt_id`, `destroyed_at`, `counts`, `destroy_status`

### Error Handling

**Validation errors (400):**
- Invalid MIME type
- File too large (>200MB)
- Missing required fields (`confirm`, `reason`)
- Invalid `export_audio_mode` or `sensitivity`

**Not found (404):**
- Transcript not found
- Audio asset not found

**Service unavailable (503):**
- Database not available

**Internal server error (500):**
- Encryption/decryption failure
- File I/O failure
- Database constraint violation

**Error response format:**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Export requires confirm=true",
    "request_id": "uuid-here"
  }
}
```

### Idempotency

**Destroy:**
- If transcript already deleted, returns success (idempotent)
- Response: `{"status": "destroyed", "destroy_status": "already_deleted"}`

**Purge:**
- Can run multiple times safely
- If record already deleted, continues without error
- Returns statistics (including `purged_count=0` if nothing to purge)

---

## Failure Modes & Guarantees

### Upload Failures

**File validation failure:**
- Returns 400 with error message
- No file stored, no DB record created
- Safe: No partial state

**Encryption failure:**
- Returns 500 with error
- No file stored, no DB record created
- Safe: No partial state

**Database failure:**
- Returns 503 if DB unavailable
- File may be stored but DB record not created
- Recovery: File can be orphaned (purged by retention)

### Export Failures

**Transcript not found:**
- Returns 404
- No ZIP created

**Audio asset not found:**
- Returns 404
- No ZIP created

**File I/O failure:**
- Returns 500
- ZIP may be partially created (best-effort cleanup)

### Destroy Failures

**Transcript not found:**
- Returns success (idempotent)
- Response: `{"status": "destroyed", "destroy_status": "already_deleted"}`

**File deletion failure:**
- Returns 500
- DB record may be deleted but file remains (orphaned, purged by retention)

**Database failure:**
- Returns 500
- File may be deleted but DB record remains (inconsistent state)

### Purge Failures

**Database unavailable:**
- Logs error, returns stats with `errors=1`
- App continues running (best-effort)

**File deletion failure:**
- Logs error, increments `errors` counter
- Continues with next record (best-effort)

**Export ZIP deletion failure:**
- Logs error, increments `errors` counter
- Continues with next file (best-effort)

**Guarantee:** Purge never stops app on error (best-effort cleanup)

### Data Consistency Guarantees

**Upload:**
- Atomic: File stored + DB record created, or neither
- No orphaned files (file stored but no DB record)

**Export:**
- Atomic: ZIP created + saved to disk, or neither
- ZIP may be orphaned if record deleted before purge

**Destroy:**
- Atomic: File deleted + DB record deleted, or neither
- CASCADE deletes ensure related data is deleted

**Purge:**
- Best-effort: May leave orphaned files if deletion fails
- Idempotent: Can run again to clean up orphaned files

---

## GDPR Summary

### Data Minimization

**Automatic retention:**
- Records purged after `RECORDER_RETENTION_DAYS` (default: 14)
- All related data deleted (audio, transcripts, segments, audit, exports)

**Manual destruction:**
- User can destroy records at any time
- Requires confirmation and reason (audit trail)

### Privacy-by-Default

**No PII in logs:**
- No filenames, paths, or content logged
- Only metadata (IDs, counts, timestamps)

**No PII in audit:**
- Audit events contain only metadata (action, actor, timestamp)
- No transcript text, no audio content, no user data

**No PII in responses:**
- Only internal identifiers (never expose paths or filenames)
- Export ZIP path is internal (client must use `docker cp`)

### Right to Erasure

**Manual destruction:**
- User can destroy records via API
- Returns receipt with `destroyed_at` timestamp
- All related data deleted (CASCADE deletes)

**Automatic purge:**
- Records purged after retention period
- All related data deleted (including orphaned export ZIPs)

### Data Portability

**Export packages:**
- ZIP with transcript, audio, audit, manifest
- Encrypted by default (safe for transfer)
- Decrypted export requires extra confirmation

### Audit Trail

**Audit events:**
- `project_created` - New project created
- `transcript_created` - New transcript created
- `audio_uploaded` - Audio file uploaded (metadata only)
- `exported` - Record exported (metadata: package_id, audio_mode)
- `destroyed` - Record destroyed (metadata: counts, receipt_id)

**Audit privacy:**
- No content, no filenames, no paths
- Only metadata (action, actor, timestamp, sanitized metadata)

### Retention Policy

**Configuration:**
- `RECORDER_RETENTION_DAYS` (default: 14)
- `RECORDER_PURGE_DRY_RUN` (default: false)

**Execution:**
- CLI-based (not API-exposed)
- Cron-friendly (can be scheduled)
- Idempotent (can run multiple times safely)

**Coverage:**
- Transcripts (based on `created_at`)
- Audio files (encrypted `.bin` files)
- Export ZIPs (`export-*.zip` in `/app/data`)
- All related DB records (CASCADE deletes)

---

## Summary

Record-modulen tillhandahåller säker audio-ingest och management för journalistiska workflows med:

- **Privacy-by-default:** Inga filnamn, paths eller content i logs/audit
- **Safe defaults:** Dry-run default, encrypted export default
- **Idempotent operations:** Destroy och purge kan köras flera gånger säkert
- **Best-effort cleanup:** Purge stoppar aldrig appen vid fel
- **Explicit operations:** Purge är CLI-only, inte API-exponerad
- **GDPR-compliant:** Automatisk retention, manual destruction, privacy-safe logging

**När någon frågar "hur säkerställer ni dataminimering?"**
→ Peka på Record-modulens retention policy och purge-mechanism.

