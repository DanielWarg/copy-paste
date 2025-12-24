# Record Module v1

Secure audio ingest and management for journalist workflow. Get audio in 10 seconds, export when ready, destroy with receipt.

## Overview

The Record module provides:
- **Fast ingest**: Create project + transcript shell in one call
- **Secure upload**: Encrypted audio storage at rest
- **Export package**: ZIP with transcript + audio + audit (no content in audit)
- **Safe destruction**: Dry-run default, confirm + receipt required

## Journalist Workflow

### 1. Create Record

```bash
POST /api/v1/record/create
Content-Type: application/json

{
  "title": "Intervju med källan",
  "sensitivity": "sensitive",
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

```bash
POST /api/v1/record/{transcript_id}/audio
Content-Type: multipart/form-data

file: [audio file]
```

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
- Computes SHA256 hash
- Stores encrypted file as `{sha256}.bin`
- Creates `AudioAsset` record
- Audit event: `audio_uploaded` (metadata: size_bytes, mime_type - NO filename)

### 3. Export Package

```bash
POST /api/v1/record/{transcript_id}/export
Content-Type: application/json

# Default: encrypted
{
  "confirm": true,
  "reason": "Export för redaktionell granskning",
  "export_audio_mode": "encrypted"
}

# Decrypted (requires extra confirmation)
{
  "confirm": true,
  "reason": "Detaljerad anledning minst 10 tecken för decrypted export",
  "export_audio_mode": "decrypted"
}
```

**Response:**
```json
{
  "status": "ok",
  "package_id": "uuid-here",
  "receipt_id": "uuid-here",
  "zip_path": "/tmp/package.zip",
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
- Audit event: `exported` (metadata: format="zip", package_id, audio_mode)

### 4. Destroy Record

```bash
POST /api/v1/record/{transcript_id}/destroy
Content-Type: application/json

# Dry run (default)
{
  "dry_run": true
}

# Confirm destruction
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
- **Two-phase destroy:**
  1. Set `destroy_status=pending` + `receipt_id`
  2. Perform deletions + set `destroy_status=destroyed`
- **Resume support:** If crash occurs, next destroy call resumes from pending
- **Destruction requires:** `confirm=true` and `reason`
- **Deletes:**
  - Audio asset (file from disk)
  - Transcript segments (if exists)
  - Transcript record
- **Audit event:** `destroyed` (metadata: counts, receipt_id)

## Security

### Privacy Protection

- **No filenames in audit/logs**: Only size_bytes, mime_type, counts
- **No paths in responses**: Only internal storage_path (never exposed)
- **No IP/user-agent/URL**: SOURCE_SAFETY_MODE enforced
- **Encrypted storage**: Files stored as `{sha256}.bin`, encrypted at rest

### Original File is Sacred

- Original filename never stored on disk
- Only SHA256 hash used as identifier
- File content encrypted before storage

### Export Safety Default

- **Default:** Audio exported as encrypted blob (`audio.bin`)
- **Decrypted export:** Requires extra confirmation + detailed reason (min 10 chars)
- **Manifest:** `manifest.json` included in ZIP with package metadata
- **Warnings:** Response includes warnings for decrypted exports

### Safe Destruction (Atomic Two-Phase)

- **Dry-run default** (shows what would be deleted)
- **Two-phase destroy:**
  1. Set `destroy_status=pending` + `receipt_id`
  2. Perform deletions + set `destroy_status=destroyed`
- **Resume support:** If crash occurs, next destroy call resumes from pending
- **Confirmation required** (`confirm=true`)
- **Reason required** (audit trail)
- **Receipt returned** (proof of destruction)

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

## Data Model

### AudioAsset

- `id`: Integer (PK)
- `project_id`: Integer (FK, nullable)
- `transcript_id`: Integer (FK, required)
- `sha256`: String (unique, indexed) - Content hash
- `mime_type`: String - Audio MIME type
- `size_bytes`: Integer - File size
- `storage_path`: String - Internal path: `{sha256}.bin`
- `created_at`: DateTime

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/record/create` | Create project + transcript shell |
| `POST` | `/api/v1/record/{transcript_id}/audio` | Upload audio file |
| `POST` | `/api/v1/record/{transcript_id}/export` | Export package (ZIP) |
| `POST` | `/api/v1/record/{transcript_id}/destroy` | Destroy record (dry_run default) |

## Examples

### Complete Workflow

```bash
# 1. Create record
RESPONSE=$(curl -X POST http://localhost:8000/api/v1/record/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Recording", "sensitivity": "standard"}')
TRANSCRIPT_ID=$(echo $RESPONSE | jq -r '.transcript_id')

# 2. Upload audio
curl -X POST http://localhost:8000/api/v1/record/$TRANSCRIPT_ID/audio \
  -F "file=@recording.wav"

# 3. Export (when ready)
curl -X POST http://localhost:8000/api/v1/record/$TRANSCRIPT_ID/export \
  -H "Content-Type: application/json" \
  -d '{"confirm": true, "reason": "Export för granskning"}'

# 4. Destroy (when done)
curl -X POST http://localhost:8000/api/v1/record/$TRANSCRIPT_ID/destroy \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "confirm": true, "reason": "Materialet är inte längre relevant"}'
```

## Testing

```bash
# Run integration tests
python3 scripts/test_record_api.py

# Test with real audio file
curl -X POST http://localhost:8000/api/v1/record/1/audio \
  -F "file=@test.wav"
```

## Privacy & Logging

- **No transcript text in logs**: Only event names, IDs, counts
- **No filenames in audit**: Only size_bytes, mime_type
- **No paths in responses**: Only internal identifiers
- **Privacy-safe**: Follows CORE logging standards

