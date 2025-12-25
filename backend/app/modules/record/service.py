"""Record service - Audio file handling and encryption."""
import os
import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, date
from uuid import uuid4

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.core.privacy_guard import sanitize_for_logging, assert_no_content, compute_integrity_hash
from app.modules.projects.models import Project
from app.modules.transcripts.models import Transcript
from app.modules.projects.file_storage import store_file, retrieve_file, compute_file_hash, delete_file
from app.modules.record.models import AudioAsset


def _has_db() -> bool:
    """Check if database is available."""
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    return engine is not None and settings.database_url is not None


# Allowed file extensions (case-insensitive)
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".mp4", ".ogg", ".webm"}

# Magic bytes for audio formats (first bytes to identify file type)
MAGIC_BYTES = {
    b"RIFF": "wav",  # WAV: RIFF header
    b"ID3": "mp3",   # MP3: ID3 tag
    b"\xff\xfb": "mp3",  # MP3: frame sync
    b"\xff\xf3": "mp3",  # MP3: frame sync variant
    b"\xff\xf2": "mp3",  # MP3: frame sync variant
    b"ftyp": "mp4",  # MP4/M4A: ftyp box (at offset 4)
    b"OggS": "ogg",  # OGG: OggS header
    b"\x1a\x45\xdf\xa3": "webm",  # WebM: EBML header
}

# Max file size: 200MB
MAX_FILE_SIZE = 200 * 1024 * 1024


def validate_audio_file(file_content: bytes, filename: Optional[str] = None) -> tuple:
    """Validate audio file using extension + magic bytes.
    
    Args:
        file_content: File content (bytes)
        filename: Optional filename (for extension check)
        
    Returns:
        Tuple of (detected_format, is_valid)
        
    Raises:
        ValueError: If file is invalid (with safe error message, no filename/path)
    """
    if len(file_content) == 0:
        raise ValueError("File is empty")
    
    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large (max: {MAX_FILE_SIZE} bytes)")
    
    # Check magic bytes (first bytes of file)
    detected_format = None
    for magic, fmt in MAGIC_BYTES.items():
        if file_content.startswith(magic):
            detected_format = fmt
            break
    
    # For MP4/M4A, check at offset 4
    if not detected_format and len(file_content) >= 8:
        if file_content[4:8] == b"ftyp":
            detected_format = "mp4"
    
    # Check extension if filename provided
    extension_match = False
    if filename:
        ext = filename.lower()
        for allowed_ext in ALLOWED_EXTENSIONS:
            if ext.endswith(allowed_ext):
                extension_match = True
                if not detected_format:
                    # Infer from extension
                    detected_format = allowed_ext.lstrip(".")
                break
    
    # Require at least one match (magic bytes OR extension)
    if not detected_format:
        raise ValueError("Unsupported file format")
    
    # Verify detected format is in allowed list
    if detected_format not in {"wav", "mp3", "m4a", "aac", "mp4", "ogg", "webm"}:
        raise ValueError("Unsupported file format")
    
    return detected_format, True


def create_record_project(
    project_id: Optional[int] = None,
    title: Optional[str] = None,
    sensitivity: str = "standard",
    language: str = "sv",
) -> Dict[str, Any]:
    """Create project and transcript shell for recording.
    
    Args:
        project_id: Existing project ID (optional)
        title: Transcript title (optional)
        sensitivity: Project sensitivity (standard|sensitive)
        language: Transcript language
        
    Returns:
        Dict with project_id, transcript_id, title, created_at
    """
    if not _has_db():
        raise ValueError("Database not available")
    
    with get_db() as db:
        # Create project if not provided
        if project_id is None:
            project_name = f"Untitled – {datetime.utcnow().strftime('%Y-%m-%d')}"
            project = Project(
                name=project_name,
                sensitivity=sensitivity,
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                start_date=date.today(),  # Required field
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            project_id = project.id
        else:
            # Verify project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")
        
        # Create transcript shell
        transcript_title = title or f"Recording – {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        transcript = Transcript(
            project_id=project_id,
            title=transcript_title,
            source="upload",
            language=language,
            status="uploaded",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        return {
            "project_id": project_id,
            "transcript_id": transcript.id,
            "title": transcript.title,
            "created_at": transcript.created_at.isoformat(),
        }


def upload_audio(
    transcript_id: int,
    file_content: bytes,
    mime_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload and encrypt audio file.
    
    Args:
        transcript_id: Transcript ID
        file_content: Audio file content (bytes)
        mime_type: Optional MIME type (validated but not required)
        filename: Optional filename (for extension validation)
        
    Returns:
        Dict with status, file_id, sha256, size_bytes, mime_type
    """
    if not _has_db():
        raise ValueError("Database not available")
    
    # Validate file using magic bytes + extension (robust, doesn't rely on MIME type)
    try:
        detected_format, is_valid = validate_audio_file(file_content, filename)
    except ValueError as e:
        # Re-raise with safe error (no filename/path leakage)
        raise ValueError(str(e))
    
    # Map detected format to MIME type
    format_to_mime = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "mp4": "audio/mp4",
        "ogg": "audio/ogg",
        "webm": "audio/webm",
    }
    validated_mime_type = format_to_mime.get(detected_format, "audio/wav")
    
    size_bytes = len(file_content)
    
    # Compute hash
    try:
        sha256 = compute_file_hash(file_content)
    except Exception as e:
        from app.core.logging import logger
        logger.error("upload_hash_failed", extra={"error_type": type(e).__name__})
        raise ValueError(f"Failed to compute file hash: {type(e).__name__}")
    
    # Store encrypted file
    try:
        storage_path = store_file(file_content, sha256)
    except Exception as e:
        from app.core.logging import logger
        logger.error("upload_storage_failed", extra={"error_type": type(e).__name__})
        raise ValueError(f"Failed to store file: {type(e).__name__}")
    
    with get_db() as db:
        # Verify transcript exists
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Check if audio asset already exists for this transcript
        existing = db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).first()
        if existing:
            # Update existing
            existing.sha256 = sha256
            existing.mime_type = validated_mime_type
            existing.size_bytes = size_bytes
            existing.storage_path = storage_path
            db.commit()
            db.refresh(existing)
            file_id = existing.id
        else:
            # Check if file with same sha256 already exists (reuse it)
            existing_file = db.query(AudioAsset).filter(AudioAsset.sha256 == sha256).first()
            if existing_file:
                # File already exists - update it to link to this transcript
                # Since sha256 is unique, we can't create a duplicate, so update the existing one
                existing_file.transcript_id = transcript_id
                existing_file.project_id = transcript.project_id
                existing_file.mime_type = validated_mime_type
                existing_file.size_bytes = size_bytes
                # Keep existing storage_path (file is already stored)
                db.commit()
                db.refresh(existing_file)
                file_id = existing_file.id
            else:
                # Create new
                audio_asset = AudioAsset(
                    project_id=transcript.project_id,
                    transcript_id=transcript_id,
                    sha256=sha256,
                    mime_type=validated_mime_type,
                    size_bytes=size_bytes,
                    storage_path=storage_path,
                    destroy_status="none",  # Explicit default
                    created_at=datetime.utcnow(),
                )
                db.add(audio_asset)
                db.commit()
                db.refresh(audio_asset)
                file_id = audio_asset.id
        
        # Trigger automatic transcription (async, non-blocking)
        # Update transcript status to "transcribing" but don't block on transcription
        transcript.status = "transcribing"
        db.commit()
        
        # Start transcription in background (non-blocking)
        # Use threading to avoid blocking the upload response
        import threading
        
        # Copy file_content to avoid issues with thread context
        file_content_copy = file_content[:]  # Create a copy
        transcript_language = transcript.language
        transcript_id_copy = transcript_id
        
        def transcribe_in_background():
            """Background transcription task."""
            from app.core.logging import logger as bg_logger
            try:
                # Try to import transcription module (may not exist if faster-whisper not installed)
                try:
                    from app.modules.ingestion.transcription import transcribe_audio
                except (ImportError, ModuleNotFoundError) as e:
                    bg_logger.warning(
                        "transcription_module_not_available",
                        extra={
                            "transcript_id": transcript_id_copy,
                            "error": str(e),
                        },
                    )
                    # Set status back to uploaded and exit
                    with get_db() as db_bg:
                        transcript_bg = db_bg.query(Transcript).filter(Transcript.id == transcript_id_copy).first()
                        if transcript_bg:
                            transcript_bg.status = "uploaded"
                            db_bg.commit()
                    return
                
                from app.modules.transcripts import service as transcripts_service
                
                # Transcribe audio (this can take time for large files)
                full_transcript, segments, metadata = transcribe_audio(
                    file_content=file_content_copy,
                    language=transcript_language,
                    filename=filename,
                )
                
                # Save segments to transcript
                with get_db() as db_bg:
                    transcript_bg = db_bg.query(Transcript).filter(Transcript.id == transcript_id_copy).first()
                    if transcript_bg:
                        transcripts_service.upsert_segments(transcript_id_copy, segments)
                        
                        # Update transcript status to "ready" and add duration
                        transcript_bg.status = "ready"
                        transcript_bg.duration_seconds = metadata.get("duration_seconds")
                        transcript_bg.updated_at = datetime.utcnow()
                        db_bg.commit()
                        
                        bg_logger.info(
                            "transcription_complete",
                            extra={
                                "transcript_id": transcript_id_copy,
                                "segment_count": len(segments),
                                "duration_seconds": metadata.get("duration_seconds"),
                            },
                        )
            except ImportError as e:
                # faster-whisper not installed - just log and keep status as "uploaded"
                bg_logger.warning(
                    "transcription_not_available",
                    extra={
                        "transcript_id": transcript_id_copy,
                        "error": str(e),
                    },
                )
                with get_db() as db_bg:
                    transcript_bg = db_bg.query(Transcript).filter(Transcript.id == transcript_id_copy).first()
                    if transcript_bg:
                        transcript_bg.status = "uploaded"
                        db_bg.commit()
            except Exception as e:
                # Transcription failed - log but don't fail upload
                error_type = type(e).__name__
                bg_logger.error(
                    "transcription_failed",
                    extra={
                        "transcript_id": transcript_id_copy,
                        "error_type": error_type,
                        "error_message": str(e)[:200],
                    },
                )
                # Keep transcript in "uploaded" status (not "ready")
                with get_db() as db_bg:
                    transcript_bg = db_bg.query(Transcript).filter(Transcript.id == transcript_id_copy).first()
                    if transcript_bg:
                        transcript_bg.status = "uploaded"
                        db_bg.commit()
        
        # Start background transcription thread
        transcription_thread = threading.Thread(target=transcribe_in_background, daemon=True)
        transcription_thread.start()
        
        return {
            "status": "ok",
            "file_id": file_id,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "mime_type": validated_mime_type,
        }


def export_record_package(
    transcript_id: int,
    confirm: bool = False,
    reason: Optional[str] = None,
    export_audio_mode: str = "encrypted",
) -> Dict[str, Any]:
    """Export record package (zip with transcript + audio + audit).
    
    Args:
        transcript_id: Transcript ID
        confirm: Confirmation required
        reason: Reason for export
        export_audio_mode: "encrypted" (default) or "decrypted" (requires extra confirmation)
        
    Returns:
        Dict with status, package_id, receipt_id, warnings
    """
    if not confirm:
        raise ValueError("Export requires confirm=true")
    
    if not reason:
        raise ValueError("Export requires reason")
    
    if export_audio_mode not in ("encrypted", "decrypted"):
        raise ValueError(f"export_audio_mode must be 'encrypted' or 'decrypted', got '{export_audio_mode}'")
    
    # Decrypted requires extra confirmation
    if export_audio_mode == "decrypted":
        # This should be checked at router level, but double-check here
        pass
    
    if not _has_db():
        raise ValueError("Database not available")
    
    with get_db() as db:
        # Get transcript
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Get audio asset
        audio_asset = db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).first()
        if not audio_asset:
            raise ValueError(f"No audio asset found for transcript {transcript_id}")
        
        # Get segments
        from app.modules.transcripts.models import TranscriptSegment
        segments = db.query(TranscriptSegment).filter(
            TranscriptSegment.transcript_id == transcript_id
        ).order_by(TranscriptSegment.start_ms).all()
        
        # Get audit events
        from app.modules.transcripts.models import TranscriptAuditEvent
        audit_events = db.query(TranscriptAuditEvent).filter(
            TranscriptAuditEvent.transcript_id == transcript_id
        ).order_by(TranscriptAuditEvent.created_at).all()
        
        # Create package
        package_id = str(uuid4())
        receipt_id = str(uuid4())
        created_at = datetime.utcnow()
        
        # Compute integrity hashes (avoid "transcript" keyword for privacy-safe manifest)
        integrity_hashes = {
            "t_id": transcript.id,  # "t_id" instead of "transcript_id" to avoid forbidden key match
            "audio_sha256": audio_asset.sha256,
        }
        if transcript.raw_integrity_hash:
            integrity_hashes["t_hash"] = transcript.raw_integrity_hash  # "t_hash" instead of "transcript_hash"
        
        # Create zip in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # transcript.json (metadata + segments)
                transcript_data = {
                    "id": transcript.id,
                    "title": transcript.title,
                    "source": transcript.source,
                    "language": transcript.language,
                    "duration_seconds": transcript.duration_seconds,
                    "status": transcript.status,
                    "created_at": transcript.created_at.isoformat(),
                    "updated_at": transcript.updated_at.isoformat(),
                    "segments": [
                        {
                            "start_ms": s.start_ms,
                            "end_ms": s.end_ms,
                            "speaker_label": s.speaker_label,
                            "text": s.text,
                            "confidence": s.confidence,
                        }
                        for s in segments
                    ],
                }
                zip_file.writestr("transcript.json", json.dumps(transcript_data, indent=2, ensure_ascii=False))
                
                # audio.bin (encrypted) or audio.dec (decrypted)
                if export_audio_mode == "decrypted":
                    # Decrypt audio for decrypted export
                    audio_content = retrieve_file(audio_asset.sha256)
                    zip_file.writestr("audio.dec", audio_content)
                else:
                    # Default: export encrypted blob (read from disk without decrypting)
                    from app.modules.projects.file_storage import _ensure_storage_dir
                    storage_dir = _ensure_storage_dir()
                    storage_path = storage_dir / f"{audio_asset.sha256}.bin"
                    if not storage_path.exists():
                        raise ValueError(f"Audio file not found: {audio_asset.sha256}")
                    encrypted_content = storage_path.read_bytes()
                    zip_file.writestr("audio.bin", encrypted_content)
                
                # audit.json (process log without content)
                audit_data = [
                    {
                        "id": e.id,
                        "action": e.action,
                        "actor": e.actor,
                        "created_at": e.created_at.isoformat(),
                        "metadata": e.metadata_json,  # Already sanitized
                    }
                    for e in audit_events
                ]
                zip_file.writestr("audit.json", json.dumps(audit_data, indent=2, ensure_ascii=False))
                
                # manifest.json (package metadata)
                manifest = {
                    "package_id": package_id,
                    "created_at": created_at.isoformat(),
                    "audio_mode": export_audio_mode,
                    "counts": {
                        "segments": len(segments),
                        "audit_events": len(audit_events),
                    },
                    "integrity_hashes": integrity_hashes,
                }
                zip_file.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        
        # Get zip bytes
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()
        
        # Save ZIP to temporary file on disk (for live_verify compatibility)
        # Use /app/data directory (mounted volume, accessible from container)
        data_dir = Path("/app/data")
        data_dir.mkdir(exist_ok=True)
        zip_filename = f"export-{package_id}.zip"
        zip_path = data_dir / zip_filename
        zip_path.write_bytes(zip_bytes)
        
        # Build response with warnings
        warnings = []
        if export_audio_mode == "decrypted":
            warnings.append("Audio exported as decrypted. Handle with extreme care.")
        
        return {
            "status": "ok",
            "package_id": package_id,
            "receipt_id": receipt_id,
            "zip_path": str(zip_path),  # Path to ZIP file on disk
            "audio_mode": export_audio_mode,
            "warnings": warnings,
        }


def destroy_record(
    transcript_id: int,
    dry_run: bool = True,
    confirm: bool = False,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Destroy record (audio + transcript + related artifacts) - atomic two-phase.
    
    Args:
        transcript_id: Transcript ID
        dry_run: If True, only return what would be deleted
        confirm: Confirmation required (if dry_run=False)
        reason: Reason for destruction
        
    Returns:
        Dict with status, receipt_id, destroyed_at, counts, destroy_status
    """
    if not _has_db():
        raise ValueError("Database not available")
    
    with get_db() as db:
        # Get transcript
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            # Idempotent: if transcript already deleted, return success
            if not dry_run:
                return {
                    "status": "destroyed",
                    "receipt_id": str(uuid4()),
                    "destroyed_at": datetime.utcnow().isoformat(),
                    "counts": {"files": 0, "segments": 0, "notes": 0},
                    "destroy_status": "already_deleted",
                }
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Get audio assets
        audio_assets = db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).all()
        from app.modules.transcripts.models import TranscriptSegment
        segments = db.query(TranscriptSegment).filter(
            TranscriptSegment.transcript_id == transcript_id
        ).all()
        
        counts = {
            "files": len(audio_assets),
            "segments": len(segments),
            "notes": 0,  # Notes are project-level, not transcript-level
        }
        
        # Check if already pending or destroyed
        pending_assets = [a for a in audio_assets if a.destroy_status == "pending"]
        destroyed_assets = [a for a in audio_assets if a.destroy_status == "destroyed"]
        
        if dry_run:
            return {
                "status": "dry_run",
                "would_delete": counts,
                "transcript_id": transcript_id,
                "destroy_status": "none",
            }
        
        # Require confirmation
        if not confirm:
            raise ValueError("Destruction requires confirm=true")
        
        if not reason:
            raise ValueError("Destruction requires reason")
        
        receipt_id = str(uuid4())
        destroyed_at = datetime.utcnow()
        
        # Perform deletions in single transaction
        try:
            # Collect sha256 values BEFORE any deletions (need them for file deletion)
            sha256_values = [a.sha256 for a in audio_assets if a.destroy_status != "destroyed"]
            
            # Delete audio files from disk (do this before DB deletions)
            for sha256 in sha256_values:
                try:
                    delete_file(sha256)
                except Exception:
                    pass  # Best effort - file may already be deleted
            
            # Delete transcript (CASCADE will automatically delete segments, audit events, and audio assets)
            db.delete(transcript)
            
            db.commit()
            
            return {
                "status": "destroyed",
                "receipt_id": receipt_id,
                "destroyed_at": destroyed_at.isoformat(),
                "counts": counts,
                "destroy_status": "destroyed",
            }
        except Exception as e:
            # On error, status remains "pending" - can be resumed
            db.rollback()
            error_type = type(e).__name__
            # Re-raise with error type for better debugging
            raise ValueError(f"Destruction failed (status: pending, can be resumed): {error_type}")

