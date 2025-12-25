"""Record router - API endpoints for audio recording and management."""
import os
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.core.config import settings
from app.core.database import get_db
from app.core.privacy_guard import sanitize_for_logging, assert_no_content
from app.modules.record import service
from app.modules.record.download import router as download_router
from app.modules.projects.models import ProjectAuditEvent
from app.modules.transcripts.models import TranscriptAuditEvent


router = APIRouter()

# Include download router (export ZIP download)
router.include_router(download_router)


# Request models
class RecordCreate(BaseModel):
    """Request model for creating record."""
    project_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=500)
    sensitivity: str = Field(default="standard", pattern="^(standard|sensitive)$")
    language: str = Field(default="sv", max_length=10)


class ExportRequest(BaseModel):
    """Request model for export."""
    confirm: bool = Field(..., description="Confirmation required")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for export")
    export_audio_mode: str = Field(default="encrypted", pattern="^(encrypted|decrypted)$", description="Audio mode: encrypted (default) or decrypted (requires extra confirmation)")


class DestroyRequest(BaseModel):
    """Request model for destruction."""
    dry_run: bool = Field(default=True, description="Dry run mode (default: true)")
    confirm: bool = Field(default=False, description="Confirmation required (if dry_run=false)")
    reason: Optional[str] = Field(None, min_length=1, max_length=500, description="Reason for destruction")


def _has_db() -> bool:
    """Check if database is available."""
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    return engine is not None and settings.database_url is not None


def _create_audit_event(
    project_id: Optional[int],
    transcript_id: int,
    action: str,
    actor: str = "system",
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Create audit event (sanitized for privacy)."""
    if not _has_db():
        return
    
    # Sanitize metadata
    if metadata:
        metadata = sanitize_for_logging(metadata, context="audit")
        assert_no_content(metadata, context="audit")
    
    with get_db() as db:
        # Get project_id from transcript if not provided
        if project_id is None:
            from app.modules.transcripts.models import Transcript
            transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
            if transcript:
                project_id = transcript.project_id
        
        # Create transcript audit event
        audit = TranscriptAuditEvent(
            transcript_id=transcript_id,
            action=action,
            actor=actor,
            created_at=datetime.utcnow(),
            metadata_json=metadata,
        )
        db.add(audit)
        
        # Create project audit event if project_id exists
        if project_id:
            project_audit = ProjectAuditEvent(
                project_id=project_id,
                action=action,
                severity="info",
                actor=actor,
                request_id=request_id,
                created_at=datetime.utcnow(),
                metadata_json=metadata,
            )
            db.add(project_audit)
        
        db.commit()


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_record(
    data: RecordCreate,
    request: Request,
) -> Dict[str, Any]:
    """Create project and transcript shell for recording.
    
    Args:
        data: Record creation data
        request: FastAPI request (for request_id)
        
    Returns:
        Created record info (project_id, transcript_id, title, created_at)
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    try:
        result = service.create_record_project(
            project_id=data.project_id,
            title=data.title,
            sensitivity=data.sensitivity,
            language=data.language,
        )
        
        # Create audit events
        request_id = getattr(request.state, "request_id", None)
        
        # Project created (if new)
        if data.project_id is None:
            _create_audit_event(
                project_id=result["project_id"],
                transcript_id=result["transcript_id"],
                action="project_created",
                actor="system",
                request_id=request_id,
                metadata={"name": result.get("title", "Untitled")},
            )
        
        # Transcript created
        _create_audit_event(
            project_id=result["project_id"],
            transcript_id=result["transcript_id"],
            action="transcript_created",
            actor="system",
            request_id=request_id,
            metadata={"title": result["title"]},
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("record_create_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create record",
        )


@router.post("/{transcript_id}/audio", status_code=status.HTTP_201_CREATED)
async def upload_audio_file(
    transcript_id: int,
    file: UploadFile = File(...),
    request: Request = None,
) -> Dict[str, Any]:
    """Upload audio file (multipart/form-data).
    
    Args:
        transcript_id: Transcript ID
        file: Audio file upload
        request: FastAPI request (for request_id)
        
    Returns:
        Upload result (status, file_id, sha256, size_bytes, mime_type)
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate and upload (validation uses magic bytes + extension, not MIME type)
        # Get filename safely (don't log it)
        filename = file.filename if hasattr(file, 'filename') else None
        
        try:
            result = service.upload_audio(
                transcript_id=transcript_id,
                file_content=file_content,
                mime_type=file.content_type,  # Optional, used for metadata only
                filename=filename,  # Optional, used for extension validation
            )
        except ValueError as e:
            # Validation failed (unsupported format, too large, etc.)
            # Return 415 Unsupported Media Type with standard error shape
            request_id = getattr(request.state, "request_id", None) if request else None
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "error": {
                        "code": "unsupported_media_type",
                        "message": "Unsupported file format",
                        "request_id": request_id,
                    }
                },
            )
        
        # Create audit event (no filename, no paths, no content_type)
        request_id = getattr(request.state, "request_id", None) if request else None
        _create_audit_event(
            project_id=None,  # Will be looked up from transcript
            transcript_id=transcript_id,
            action="audio_uploaded",
            actor="system",
            request_id=request_id,
            metadata={
                "size_bytes": result["size_bytes"],
                # mime_type excluded from audit (privacy-safe)
            },
        )
        
        return result
    except HTTPException:
        # Re-raise HTTPExceptions (including our 415)
        raise
    except Exception as e:
        # Safe debug logging: exception type and message only, no payload/secrets
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)[:200] if len(str(e)) <= 200 else str(e)[:200] + "..."
        logger.error(
            "audio_upload_failed",
            extra={
                "error_type": error_type,
                "error_message": error_msg,
            },
        )
        # Always log full traceback to stderr for debugging (not in response)
        import sys
        print(f"DEBUG: Upload failed: {error_type}: {error_msg}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload audio",
        )


@router.post("/{transcript_id}/export")
async def export_record(
    transcript_id: int,
    data: ExportRequest,
    request: Request,
) -> Dict[str, Any]:
    """Export record package (zip with transcript + audio + audit).
    
    Args:
        transcript_id: Transcript ID
        data: Export request (confirm, reason, export_audio_mode)
        request: FastAPI request (for request_id)
        
    Returns:
        ZIP file as bytes with Content-Type: application/zip
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    # Extra confirmation for decrypted export
    if data.export_audio_mode == "decrypted":
        if not data.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decrypted export requires confirm=true and explicit reason",
            )
        if not data.reason or len(data.reason) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decrypted export requires detailed reason (min 10 characters)",
            )
    
    try:
        result = service.export_record_package(
            transcript_id=transcript_id,
            confirm=data.confirm,
            reason=data.reason,
            export_audio_mode=data.export_audio_mode,
        )
        
        # Create audit event
        request_id = getattr(request.state, "request_id", None)
        audit_metadata = {
            "format": "zip",
            "package_id": result["package_id"],
            "audio_mode": result["audio_mode"],
        }
        _create_audit_event(
            project_id=None,
            transcript_id=transcript_id,
            action="exported",
            actor="system",
            request_id=request_id,
            metadata=audit_metadata,
        )
        
        # Return JSON response with zip_path (for live_verify compatibility)
        return {
            "status": result["status"],
            "package_id": result["package_id"],
            "receipt_id": result["receipt_id"],
            "zip_path": result["zip_path"],
            "audio_mode": result["audio_mode"],
            "warnings": result.get("warnings", []),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("export_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export record",
        )


@router.post("/{transcript_id}/destroy")
async def destroy_record(
    transcript_id: int,
    data: DestroyRequest,
    request: Request,
) -> Dict[str, Any]:
    """Destroy record (audio + transcript + related artifacts).
    
    Args:
        transcript_id: Transcript ID
        data: Destroy request (dry_run, confirm, reason)
        request: FastAPI request (for request_id)
        
    Returns:
        Destruction result (status, receipt_id, destroyed_at, counts)
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    try:
        result = service.destroy_record(
            transcript_id=transcript_id,
            dry_run=data.dry_run,
            confirm=data.confirm,
            reason=data.reason,
        )
        
        # Note: Audit event for "destroyed" is not created here because transcript is already deleted
        # Audit events are CASCADE-deleted when transcript is deleted, so we can't create them after deletion
        # If audit trail is needed, it should be created BEFORE deletion in service layer
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        # ValueError from service (validation errors)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log exception type for debugging
        error_type = type(e).__name__
        logger.error("destroy_failed", extra={"error_type": error_type})
        # In debug mode, include error type in response
        if settings.debug:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to destroy record: {error_type}",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to destroy record",
        )

