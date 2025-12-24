"""GDPR-compliant retention purge for Record module.

Privacy-safe: No content, no paths, no PII in logs.
Idempotent: Can run multiple times safely.
Best-effort: Never raises exceptions that stop the app.

Purges:
- Expired transcripts (based on created_at)
- Audio files (encrypted .bin files)
- Export ZIP files (export-*.zip in /app/data)
- All related DB records (CASCADE deletes)
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.modules.record.models import AudioAsset
from app.modules.transcripts.models import Transcript
from app.modules.projects.file_storage import delete_file


def purge_expired_records(dry_run: bool = None, retention_days: int = None) -> Dict[str, Any]:
    """Purge records older than retention period.
    
    Args:
        dry_run: If True, only log what would be deleted (default: settings.recorder_purge_dry_run)
        retention_days: Override retention days (default: settings.recorder_retention_days)
        
    Returns:
        Dict with purge statistics (purged_count, files_deleted, exports_deleted, errors)
    """
    if dry_run is None:
        dry_run = settings.recorder_purge_dry_run
    
    if retention_days is None:
        retention_days = settings.recorder_retention_days
    
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    stats = {
        "purged_count": 0,
        "files_deleted": 0,
        "exports_deleted": 0,
        "errors": 0,
        "dry_run": dry_run,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
    }
    
    if not settings.database_url:
        logger.info("record_purge_skipped", extra={"reason": "database_not_configured"})
        return stats
    
    try:
        with get_db() as db:
            # Find expired transcripts (created before cutoff_date)
            expired_transcripts = db.query(Transcript).filter(
                Transcript.created_at < cutoff_date
            ).all()
            
            if not expired_transcripts:
                logger.info("record_purge_complete", extra={
                    "purged_count": 0,
                    "dry_run": dry_run,
                })
                return stats
            
            logger.info("record_purge_start", extra={
                "expired_count": len(expired_transcripts),
                "dry_run": dry_run,
                "retention_days": retention_days,
            })
            
            for transcript in expired_transcripts:
                transcript_id = transcript.id
                age_days = (datetime.utcnow() - transcript.created_at).days
                
                try:
                    # Get audio assets for this transcript
                    audio_assets = db.query(AudioAsset).filter(
                        AudioAsset.transcript_id == transcript_id
                    ).all()
                    
                    # Collect sha256 values for file deletion
                    sha256_values = [a.sha256 for a in audio_assets]
                    
                    if dry_run:
                        # Log what would be purged (privacy-safe)
                        logger.info("record_purge_candidate", extra={
                            "transcript_id": transcript_id,
                            "age_days": age_days,
                            "audio_files_count": len(sha256_values),
                            "reason": "retention_expired",
                        })
                        stats["purged_count"] += 1
                        stats["files_deleted"] += len(sha256_values)
                    else:
                        # Delete audio files from disk (best-effort)
                        for sha256 in sha256_values:
                            try:
                                delete_file(sha256)
                                stats["files_deleted"] += 1
                            except Exception:
                                # Best effort - file may already be deleted
                                stats["errors"] += 1
                                pass
                        
                        # Delete transcript (CASCADE will delete segments, audit events, audio assets)
                        db.delete(transcript)
                        db.commit()
                        
                        # Log purge (privacy-safe: no content, no paths)
                        logger.info("record_purged", extra={
                            "transcript_id": transcript_id,
                            "age_days": age_days,
                            "reason": "retention_expired",
                            "files_deleted": len(sha256_values),
                        })
                        stats["purged_count"] += 1
                
                except Exception as e:
                    # Best effort - log error but continue with next record
                    error_type = type(e).__name__
                    logger.error("record_purge_failed", extra={
                        "transcript_id": transcript_id,
                        "error_type": error_type,
                    })
                    stats["errors"] += 1
                    db.rollback()
                    continue
            
            # Clean up orphaned export ZIP files in /app/data (older than retention)
            try:
                _purge_orphaned_exports(cutoff_date, dry_run, stats)
            except Exception as e:
                # Best effort - log but don't fail
                logger.error("export_purge_failed", extra={"error_type": type(e).__name__})
                stats["errors"] += 1
            
            logger.info("record_purge_complete", extra={
                "purged_count": stats["purged_count"],
                "files_deleted": stats["files_deleted"],
                "exports_deleted": stats["exports_deleted"],
                "errors": stats["errors"],
                "dry_run": dry_run,
            })
            
            return stats
    
    except Exception as e:
        # Never fail the app - log and return stats
        error_type = type(e).__name__
        logger.error("record_purge_critical_failed", extra={"error_type": error_type})
        stats["errors"] += 1
        return stats


def _purge_orphaned_exports(cutoff_date: datetime, dry_run: bool, stats: Dict[str, Any]) -> None:
    """Purge orphaned export ZIP files older than cutoff_date.
    
    Export ZIPs are created in /app/data/export-{package_id}.zip.
    Since package_id is not stored in DB, we purge based on file mtime.
    This covers both:
    - Export ZIPs for purged records (orphaned after record deletion)
    - Export ZIPs for records that were destroyed before purge
    
    Args:
        cutoff_date: Delete files older than this date
        dry_run: If True, only log what would be deleted
        stats: Stats dict to update
    """
    data_dir = Path("/app/data")
    if not data_dir.exists():
        return
    
    # Find export-*.zip files
    export_files = list(data_dir.glob("export-*.zip"))
    
    for zip_path in export_files:
        try:
            # Check file modification time
            mtime = datetime.fromtimestamp(zip_path.stat().st_mtime)
            if mtime < cutoff_date:
                if dry_run:
                    logger.info("export_purge_candidate", extra={
                        "file_age_days": (datetime.utcnow() - mtime).days,
                        "reason": "retention_expired",
                    })
                    stats["exports_deleted"] += 1
                else:
                    zip_path.unlink()
                    logger.info("export_orphan_purged", extra={
                        "file_age_days": (datetime.utcnow() - mtime).days,
                        "reason": "retention_expired",
                    })
                    stats["exports_deleted"] += 1
        except Exception:
            # Best effort - file may not exist or be inaccessible
            pass

