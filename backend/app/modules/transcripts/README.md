# Transcripts Module

Journalist-ready transcript management with segment timestamps, speaker labels, confidence scores, search/filter, and export (SRT/VTT/Quotes).

## Overview

The Transcripts module provides a complete solution for storing, managing, and exporting transcripts. It supports:

- **Segmented transcripts** with timestamps (start_ms, end_ms)
- **Speaker labels** for multi-speaker transcripts
- **Confidence scores** for transcription quality
- **Search and filtering** by title, speaker, text, status, language, source, date
- **Export formats**: SRT (subtitles), VTT (WebVTT), Quotes (simple list)
- **Audit trail** (NO transcript text, only metadata)
- **DB-optional**: Works with memory store if DB unavailable

## Journalist Workflow

### 1. List Transcripts

```bash
GET /api/v1/transcripts?q=interview&status=ready&limit=50
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Intervju: Kommunalrådet om skolnedläggningen",
      "source": "interview",
      "language": "sv",
      "duration_seconds": 840,
      "status": "ready",
      "created_at": "2025-12-23T10:00:00",
      "updated_at": "2025-12-23T10:05:00",
      "segments_count": 42,
      "preview": "Det är ett tufft beslut, men vi måste se till ekonomin..."
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### 2. Open Transcript

```bash
GET /api/v1/transcripts/1?include_segments=true
```

**Response:**
```json
{
  "id": 1,
  "title": "Intervju: Kommunalrådet om skolnedläggningen",
  "source": "interview",
  "language": "sv",
  "duration_seconds": 840,
  "status": "ready",
  "created_at": "2025-12-23T10:00:00",
  "updated_at": "2025-12-23T10:05:00",
  "segments": [
    {
      "id": 1,
      "start_ms": 0,
      "end_ms": 3500,
      "speaker_label": "SPEAKER_1",
      "text": "Det är ett tufft beslut, men vi måste se till ekonomin.",
      "confidence": 0.95,
      "created_at": "2025-12-23T10:05:00"
    }
  ]
}
```

### 3. View Segments

Segments are ordered by `start_ms` and include:
- **Timestamps**: `start_ms` and `end_ms` (milliseconds)
- **Speaker**: `speaker_label` (e.g., "SPEAKER_1", "SPEAKER_2")
- **Text**: Full segment text
- **Confidence**: 0.0-1.0 (optional)

### 4. Export

**SRT (Subtitles):**
```bash
POST /api/v1/transcripts/1/export?format=srt
```

**Response:**
```json
{
  "format": "srt",
  "content": "1\n00:00:00,000 --> 00:00:03,500\nDet är ett tufft beslut...\n\n2\n00:00:03,500 --> 00:00:07,200\nMen vad säger föräldrarna?...\n"
}
```

**VTT (WebVTT):**
```bash
POST /api/v1/transcripts/1/export?format=vtt
```

**Response:**
```json
{
  "format": "vtt",
  "content": "WEBVTT\n\n00:00:00.000 --> 00:00:03.500\n<v SPEAKER_1>Det är ett tufft beslut...\n"
}
```

**Quotes (Simple List):**
```bash
POST /api/v1/transcripts/1/export?format=quotes
```

**Response:**
```json
{
  "format": "quotes",
  "items": [
    {
      "speaker": "SPEAKER_1",
      "start_ms": 0,
      "end_ms": 3500,
      "text": "Det är ett tufft beslut, men vi måste se till ekonomin."
    }
  ]
}
```

## API Endpoints

### List / Search

**GET** `/api/v1/transcripts`

**Query Parameters:**
- `q` (optional): Search in title, speaker_label, segment text
- `status` (optional): Filter by status (uploaded|transcribing|ready|reviewed|archived|deleted)
- `language` (optional): Filter by language code
- `source` (optional): Filter by source (interview|meeting|upload)
- `date_from` (optional): Filter from date (ISO format)
- `date_to` (optional): Filter to date (ISO format)
- `limit` (default: 50, max: 200): Max items
- `offset` (default: 0): Pagination offset

**Response:** List of transcripts with preview and segments_count

### Get Transcript

**GET** `/api/v1/transcripts/{id}`

**Query Parameters:**
- `include_segments` (default: true): Include segments in response

**Response:** Full transcript with optional segments

### Create Transcript

**POST** `/api/v1/transcripts`

**Body:**
```json
{
  "title": "Interview Title",
  "source": "interview",
  "language": "sv",
  "duration_seconds": 840,
  "status": "uploaded"
}
```

**Response:** Created transcript (without segments)

### Upsert Segments

**POST** `/api/v1/transcripts/{id}/segments`

**Body:**
```json
{
  "segments": [
    {
      "start_ms": 0,
      "end_ms": 5000,
      "speaker_label": "SPEAKER_1",
      "text": "Segment text here",
      "confidence": 0.95
    }
  ]
}
```

**Behavior:** Replaces all existing segments for the transcript.

**Validation:**
- `start_ms` must be < `end_ms`
- Segments are sorted by `start_ms` automatically

**Response:**
```json
{
  "status": "ok",
  "segments_saved": 1
}
```

### Export Transcript

**POST** `/api/v1/transcripts/{id}/export?format={srt|vtt|quotes}`

**Response:** Format-specific export data

### Delete Transcript

**DELETE** `/api/v1/transcripts/{id}`

**Response:**
```json
{
  "status": "deleted",
  "receipt_id": "uuid-here",
  "deleted_at": "2025-12-23T10:10:00"
}
```

**Behavior:** Hard delete (removes transcript and all segments)

## No-DB Mode

If `DATABASE_URL` is not set, the module uses an in-memory store with seed data:

- **2-3 sample transcripts** with segments
- **Same API shapes** as DB mode
- **List/Get/Export** work normally
- **Create/Segments** work but data is not persisted

This ensures UI works even without database for development.

## Data Model

### Transcript

- `id`: Integer (PK)
- `title`: String (indexed)
- `source`: String (indexed) - "interview", "meeting", "upload"
- `language`: String (indexed, default "sv")
- `duration_seconds`: Integer (nullable)
- `status`: String (indexed) - uploaded|transcribing|ready|reviewed|archived|deleted
- `created_at`: DateTime (indexed)
- `updated_at`: DateTime

### TranscriptSegment

- `id`: Integer (PK)
- `transcript_id`: Foreign Key -> transcripts.id (indexed)
- `start_ms`: Integer (indexed)
- `end_ms`: Integer
- `speaker_label`: String (indexed) - "SPEAKER_1", "SPEAKER_2", etc.
- `text`: Text (full segment text)
- `confidence`: Float (0.0-1.0, nullable)
- `created_at`: DateTime

### TranscriptAuditEvent

- `id`: Integer (PK)
- `transcript_id`: Foreign Key (indexed)
- `action`: String (indexed) - created|updated|segments_upserted|exported|deleted
- `actor`: String (nullable, default "system")
- `created_at`: DateTime
- `metadata_json`: JSON (nullable) - **STRICT: NO transcript text, only counts/format/id**

## Privacy & Logging

- **No transcript text in logs**: Only event names, IDs, counts
- **No transcript text in audit metadata**: Only counts, format, IDs
- **Privacy-safe**: Follows CORE logging standards

## Examples

### Create and Populate Transcript

```bash
# Create transcript
curl -X POST http://localhost:8000/api/v1/transcripts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Interview",
    "source": "interview",
    "language": "sv"
  }'

# Response: {"id": 1, "title": "Test Interview", ...}

# Add segments
curl -X POST http://localhost:8000/api/v1/transcripts/1/segments \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {
        "start_ms": 0,
        "end_ms": 5000,
        "speaker_label": "SPEAKER_1",
        "text": "Hello, this is a test.",
        "confidence": 0.95
      }
    ]
  }'

# Export as SRT
curl "http://localhost:8000/api/v1/transcripts/1/export?format=srt"
```

### Search Transcripts

```bash
# Search by text
curl "http://localhost:8000/api/v1/transcripts?q=ekonomi"

# Filter by status
curl "http://localhost:8000/api/v1/transcripts?status=ready"

# Filter by date range
curl "http://localhost:8000/api/v1/transcripts?date_from=2025-12-01&date_to=2025-12-31"
```

## Status Values

- `uploaded`: Transcript uploaded, awaiting transcription
- `transcribing`: Transcription in progress
- `ready`: Transcription complete, ready for review
- `reviewed`: Reviewed by journalist
- `archived`: Archived (not deleted)
- `deleted`: Deleted (hard delete removes from DB)

## Export Formats

### SRT (SubRip)

Standard subtitle format with numbered cues:
```
1
00:00:00,000 --> 00:00:03,500
Text here

2
00:00:03,500 --> 00:00:07,200
More text
```

### VTT (WebVTT)

Web Video Text Tracks format:
```
WEBVTT

00:00:00.000 --> 00:00:03.500
<v SPEAKER_1>Text here
```

### Quotes

Simple JSON list with speaker and timestamps:
```json
{
  "format": "quotes",
  "items": [
    {
      "speaker": "SPEAKER_1",
      "start_ms": 0,
      "end_ms": 3500,
      "text": "Text here"
    }
  ]
}
```

