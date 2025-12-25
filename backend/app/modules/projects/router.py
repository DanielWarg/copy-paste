"""Projects router - API endpoints for project management."""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Query, HTTPException, status, Request, UploadFile, File
from pydantic import BaseModel, Field, field_validator

from app.core.logging import logger
from app.core.config import settings
from app.core import database
from app.core.database import get_db
from app.core.privacy_guard import sanitize_for_logging, assert_no_content
from app.modules.projects.models import Project, ProjectNote, ProjectFile, ProjectAuditEvent
from app.modules.projects.integrity import verify_project_integrity
from app.modules.projects.file_storage import store_file, compute_file_hash
from app.modules.transcripts.models import Transcript


router = APIRouter()


# File validation constants
ALLOWED_PROJECT_FILE_EXTENSIONS = {".txt", ".docx", ".pdf"}
MAX_PROJECT_FILE_SIZE = 25 * 1024 * 1024  # 25MB

# Magic bytes for document formats
PROJECT_FILE_MAGIC_BYTES = {
    b"%PDF": "pdf",  # PDF: starts with %PDF
    b"PK\x03\x04": "docx",  # DOCX: ZIP-based format (Office Open XML)
}


def validate_project_file(file_content: bytes, filename: Optional[str] = None) -> tuple:
    """Validate project file using extension + magic bytes.
    
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
    
    if len(file_content) > MAX_PROJECT_FILE_SIZE:
        raise ValueError(f"File too large (max: {MAX_PROJECT_FILE_SIZE} bytes)")
    
    # Check magic bytes (first bytes of file)
    detected_format = None
    for magic, fmt in PROJECT_FILE_MAGIC_BYTES.items():
        if file_content.startswith(magic):
            detected_format = fmt
            break
    
    # For DOCX, check at offset 0 (ZIP header)
    if not detected_format and len(file_content) >= 4:
        if file_content[:4] == b"PK\x03\x04":
            detected_format = "docx"
    
    # Check extension if filename provided
    if filename:
        ext = filename.lower()
        for allowed_ext in ALLOWED_PROJECT_FILE_EXTENSIONS:
            if ext.endswith(allowed_ext):
                if not detected_format:
                    # Infer from extension
                    detected_format = allowed_ext.lstrip(".")
                break
    
    # For TXT files, we accept if extension matches (no magic bytes for plain text)
    if filename and filename.lower().endswith(".txt"):
        if not detected_format:
            detected_format = "txt"
    
    # Require at least one match (magic bytes OR extension)
    if not detected_format:
        raise ValueError("Unsupported file format. Allowed: .txt, .docx, .pdf")
    
    # Verify detected format is in allowed list
    if detected_format not in {"txt", "docx", "pdf"}:
        raise ValueError("Unsupported file format. Allowed: .txt, .docx, .pdf")
    
    return detected_format, True


# Request/Response models
class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: Optional[str] = Field(None, max_length=500)
    sensitivity: str = Field(default="standard", pattern="^(standard|sensitive)$")
    start_date: Optional[date] = Field(None, description="Project start date (defaults to today)")
    due_date: Optional[date] = Field(None, description="Project deadline (optional)")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate that due_date is not before start_date."""
        if v is None:
            return v
        
        start_date = info.data.get('start_date') or date.today()
        if v < start_date:
            raise ValueError("due_date cannot be before start_date")
        return v


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, max_length=500)
    sensitivity: Optional[str] = Field(None, pattern="^(standard|sensitive)$")
    status: Optional[str] = Field(None, pattern="^(active|archived)$")
    start_date: Optional[date] = Field(None, description="Project start date")
    due_date: Optional[date] = Field(None, description="Project deadline (optional)")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate that due_date is not before start_date."""
        if v is None:
            return v
        
        # If start_date is also being updated, use that; otherwise we'll check against existing project
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError("due_date cannot be before start_date")
        return v


class ProjectAttach(BaseModel):
    """Request model for attaching transcripts to project."""
    transcript_ids: List[int] = Field(..., min_items=1)


def _has_db() -> bool:
    """Check if database is available."""
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    has_engine = engine is not None
    has_url = settings.database_url is not None
    if not has_engine:
        logger.warning("db_check_failed", extra={"engine_is_none": True, "database_url_set": has_url})
    return has_engine and has_url


def _get_project_counts(project_id: int) -> Dict[str, Any]:
    """Get counts for a project."""
    if not _has_db():
        return {
            "transcripts_count": 0,
            "notes_count": 0,
            "files_count": 0,
            "last_activity_at": None,
        }
    
    with get_db() as db:
        transcripts_count = db.query(Transcript).filter(Transcript.project_id == project_id).count()
        notes_count = db.query(ProjectNote).filter(ProjectNote.project_id == project_id).count()
        files_count = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).count()
        
        # Get last activity (max of updated_at from all artifacts)
        last_activity = None
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            last_activity = project.updated_at
        
        # Check notes
        latest_note = db.query(ProjectNote).filter(
            ProjectNote.project_id == project_id
        ).order_by(ProjectNote.updated_at.desc()).first()
        if latest_note and (not last_activity or latest_note.updated_at > last_activity):
            last_activity = latest_note.updated_at
        
        # Check files
        latest_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id
        ).order_by(ProjectFile.created_at.desc()).first()
        if latest_file and (not last_activity or latest_file.created_at > last_activity):
            last_activity = latest_file.created_at
        
        # Check transcripts
        latest_transcript = db.query(Transcript).filter(
            Transcript.project_id == project_id
        ).order_by(Transcript.updated_at.desc()).first()
        if latest_transcript and (not last_activity or latest_transcript.updated_at > last_activity):
            last_activity = latest_transcript.updated_at
        
        return {
            "transcripts_count": transcripts_count,
            "notes_count": notes_count,
            "files_count": files_count,
            "last_activity_at": last_activity.isoformat() if last_activity else None,
        }


def _create_audit_event(
    project_id: int,
    action: str,
    actor: str = "system",
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    severity: str = "info",
) -> None:
    """Create audit event (NO CONTENT, only metadata).
    
    Args:
        project_id: Project ID
        action: Action type (created|updated|file_uploaded|etc)
        actor: Actor (system|user)
        request_id: Request ID (for correlation)
        metadata: Metadata dict (STRICT: counts, ids, format - NEVER content/filenames)
        severity: Severity (info|warning|critical)
    """
    if not _has_db():
        return
    
    # Sanitize metadata (ensure no content/filenames)
    sanitized_metadata = sanitize_for_logging(metadata or {})
    
    with get_db() as db:
        audit = ProjectAuditEvent(
            project_id=project_id,
            action=action,
            severity=severity,
            actor=actor,
            request_id=request_id,
            metadata_json=sanitized_metadata,
            created_at=datetime.utcnow(),
        )
        db.add(audit)
        db.commit()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    request: Request,
) -> Dict[str, Any]:
    """Create a new project.
    
    Args:
        data: Project creation data
        request: FastAPI request (for request_id)
        
    Returns:
        Created project with counts
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    # Default name if not provided
    name = data.name or f"Untitled – {datetime.utcnow().strftime('%Y-%m-%d')}"
    
    # Default start_date to today if not provided
    start_date = data.start_date or date.today()
    
    with get_db() as db:
        project = Project(
            name=name,
            sensitivity=data.sensitivity,
            status="active",
            start_date=start_date,
            due_date=data.due_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Create audit event
        request_id = getattr(request.state, "request_id", None)
        _create_audit_event(
            project_id=project.id,
            action="created",
            actor="system",
            request_id=request_id,
            metadata={"name": name, "sensitivity": data.sensitivity},
        )
        
        # Get counts
        counts = _get_project_counts(project.id)
        
        return {
            "id": project.id,
            "name": project.name,
            "sensitivity": project.sensitivity,
            "status": project.status,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            **counts,
        }


@router.get("/")
async def list_projects(
    q: Optional[str] = Query(None, description="Search in name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sensitivity: Optional[str] = Query(None, description="Filter by sensitivity"),
    limit: int = Query(50, ge=1, le=200, description="Max items"),
    offset: int = Query(0, ge=0, description="Offset"),
) -> Dict[str, Any]:
    """List projects with optional filters.
    
    Args:
        q: Search query (name)
        status: Filter by status
        sensitivity: Filter by sensitivity
        limit: Max items
        offset: Offset
        
    Returns:
        List of projects with counts
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    with get_db() as db:
        query = db.query(Project)
        
        # Filters
        if q:
            query = query.filter(Project.name.ilike(f"%{q}%"))
        if status:
            query = query.filter(Project.status == status)
        if sensitivity:
            query = query.filter(Project.sensitivity == sensitivity)
        
        # Get total
        total = query.count()
        
        # Pagination
        projects = query.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()
        
        # Build response with counts
        items = []
        for project in projects:
            counts = _get_project_counts(project.id)
            items.append({
                "id": project.id,
                "name": project.name,
                "sensitivity": project.sensitivity,
                "status": project.status,
                "start_date": project.start_date.isoformat() if project.start_date else None,
                "due_date": project.due_date.isoformat() if project.due_date else None,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                **counts,
            })
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/{project_id}")
async def get_project(project_id: int) -> Dict[str, Any]:
    """Get project by ID.
    
    Args:
        project_id: Project ID
        
    Returns:
        Project with counts
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    with get_db() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
        
        counts = _get_project_counts(project.id)
        
        return {
            "id": project.id,
            "name": project.name,
            "sensitivity": project.sensitivity,
            "status": project.status,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "started_working_at": project.started_working_at.isoformat() if project.started_working_at else None,
            **counts,
        }


@router.patch("/{project_id}")
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    request: Request,
) -> Dict[str, Any]:
    """Update project (name, sensitivity, status, dates).
    
    Args:
        project_id: Project ID
        data: Update data
        request: FastAPI request (for request_id)
        
    Returns:
        Updated project
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    with get_db() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
        
        # Track changes
        changed_fields = []
        
        # Validate due_date against start_date (if both are being updated)
        if data.due_date is not None:
            check_start_date = data.start_date if data.start_date is not None else project.start_date
            if check_start_date and data.due_date < check_start_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="due_date cannot be before start_date",
                )
        
        if data.name is not None and data.name != project.name:
            project.name = data.name
            changed_fields.append("name")
        
        if data.sensitivity is not None and data.sensitivity != project.sensitivity:
            project.sensitivity = data.sensitivity
            changed_fields.append("sensitivity")
        
        if data.status is not None and data.status != project.status:
            project.status = data.status
            changed_fields.append("status")
        
        if data.start_date is not None and data.start_date != project.start_date:
            # Validate that due_date (if set) is not before new start_date
            if project.due_date and project.due_date < data.start_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot set start_date after due_date. Update due_date first or set it to None.",
                )
            project.start_date = data.start_date
            changed_fields.append("start_date")
        
        if data.due_date is not None and data.due_date != project.due_date:
            project.due_date = data.due_date
            changed_fields.append("due_date")
        
        if changed_fields:
            project.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(project)
            
            # Create audit event
            request_id = getattr(request.state, "request_id", None)
            _create_audit_event(
                project_id=project.id,
                action="updated",
                actor="system",
                request_id=request_id,
                metadata={"changed_fields": changed_fields},
            )
        
        counts = _get_project_counts(project.id)
        
        return {
            "id": project.id,
            "name": project.name,
            "sensitivity": project.sensitivity,
            "status": project.status,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "started_working_at": project.started_working_at.isoformat() if project.started_working_at else None,
            **counts,
        }


@router.get("/{project_id}/verify")
async def verify_project(project_id: int) -> Dict[str, Any]:
    """Verify project integrity.
    
    Args:
        project_id: Project ID
        
    Returns:
        Integrity verification result
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    result = verify_project_integrity(project_id)
    
    # Sanitize issues (no content/filenames)
    issues = result.get("issues", [])
    sanitized_issues = []
    for issue in issues:
        sanitized_issue = sanitize_for_logging(issue)
        sanitized_issues.append(sanitized_issue)
    
    return {
        "project_id": project_id,
        "status": result.get("status", "unknown"),
        "issues": sanitized_issues,
    }


@router.post("/{project_id}/attach")
async def attach_transcripts(
    project_id: int,
    data: ProjectAttach,
    request: Request,
) -> Dict[str, Any]:
    """Attach transcripts to project.
    
    Args:
        project_id: Project ID
        data: Transcript IDs to attach
        request: FastAPI request (for request_id)
        
    Returns:
        Attachment result
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    with get_db() as db:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
        
        # Verify transcripts exist
        transcripts = db.query(Transcript).filter(Transcript.id.in_(data.transcript_ids)).all()
        found_ids = {t.id for t in transcripts}
        missing_ids = set(data.transcript_ids) - found_ids
        
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcripts not found: {list(missing_ids)}",
            )
        
        # Attach transcripts
        attached_count = 0
        for transcript in transcripts:
            if transcript.project_id != project_id:
                transcript.project_id = project_id
                attached_count += 1
        
        # Set started_working_at if not set
        if attached_count > 0 and not project.started_working_at:
            project.started_working_at = datetime.utcnow()
        
        project.updated_at = datetime.utcnow()
        db.commit()
        
        # Create audit event
        request_id = getattr(request.state, "request_id", None)
        _create_audit_event(
            project_id=project.id,
            action="transcripts_attached",
            actor="system",
            request_id=request_id,
            metadata={"transcripts_count": attached_count, "transcript_ids": list(found_ids)},
        )
        
        return {
            "status": "ok",
            "attached_count": attached_count,
            "transcript_ids": list(found_ids),
        }


@router.get("/security-status")
async def get_security_status() -> Dict[str, Any]:
    """Get security status (minimal, no paths/hosts).
    
    Returns:
        Security status
    """
    return {
        "source_safety_mode": settings.source_safety_mode,
        "retention_defaults": {
            "default_days": settings.retention_days_default,
            "sensitive_days": settings.retention_days_sensitive,
            "temp_file_ttl_hours": settings.temp_file_ttl_hours,
        },
        "audit_enabled": True,  # Always enabled
        "encryption_enabled": bool(os.getenv("PROJECT_FILES_KEY")),  # Check if key is set
    }


@router.post("/{project_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    request: Request = None,
) -> Dict[str, Any]:
    """Upload file to project (multipart/form-data).
    
    Allowed formats: .txt, .docx, .pdf
    Max size: 25MB
    
    Args:
        project_id: Project ID
        file: File upload
        request: FastAPI request (for request_id)
        
    Returns:
        Upload result (file_id, sha256, size_bytes, mime_type, created_at)
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Get filename safely (don't log it)
        filename = file.filename if hasattr(file, 'filename') else None
        
        # Validate file (magic bytes + extension)
        try:
            detected_format, is_valid = validate_project_file(file_content, filename)
        except ValueError as e:
            request_id = getattr(request.state, "request_id", None) if request else None
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "error": {
                        "code": "unsupported_media_type",
                        "message": str(e),
                        "request_id": request_id,
                    }
                },
            )
        
        # Map detected format to MIME type
        format_to_mime = {
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
        }
        validated_mime_type = format_to_mime.get(detected_format, "application/octet-stream")
        
        size_bytes = len(file_content)
        
        # Compute hash
        try:
            sha256 = compute_file_hash(file_content)
        except Exception as e:
            logger.error("project_file_hash_failed", extra={"error_type": type(e).__name__})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to compute file hash",
            )
        
        # Store encrypted file
        try:
            storage_path = store_file(file_content, sha256)
        except Exception as e:
            logger.error("project_file_storage_failed", extra={"error_type": type(e).__name__})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store file",
            )
        
        with get_db() as db:
            # Verify project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project {project_id} not found",
                )
            
            # Check if file already exists (by sha256)
            existing_file = db.query(ProjectFile).filter(ProjectFile.sha256 == sha256).first()
            if existing_file:
                # File already exists, return existing record
                return {
                    "file_id": existing_file.id,
                    "sha256": existing_file.sha256,
                    "size_bytes": existing_file.size_bytes,
                    "mime_type": existing_file.mime_type,
                    "created_at": existing_file.created_at.isoformat(),
                }
            
            # Create ProjectFile record
            project_file = ProjectFile(
                project_id=project_id,
                original_filename=filename or "unnamed",  # Only in DB, never on disk
                sha256=sha256,
                mime_type=validated_mime_type,
                size_bytes=size_bytes,
                stored_encrypted=True,
                storage_path=storage_path,
                created_at=datetime.utcnow(),
            )
            db.add(project_file)
            
            # Set started_working_at if not set
            if not project.started_working_at:
                project.started_working_at = datetime.utcnow()
            
            project.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(project_file)
            
            # Create audit event (NO filename, NO content)
            request_id = getattr(request.state, "request_id", None) if request else None
            _create_audit_event(
                project_id=project_id,
                action="file_uploaded",
                actor="system",
                request_id=request_id,
                metadata={
                    "file_id": project_file.id,
                    "size_bytes": size_bytes,
                    "mime_type": validated_mime_type,
                    # NO filename, NO content
                },
            )
            
            return {
                "file_id": project_file.id,
                "sha256": project_file.sha256,
                "size_bytes": project_file.size_bytes,
                "mime_type": project_file.mime_type,
                "created_at": project_file.created_at.isoformat(),
            }
    
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(
            "project_file_upload_failed",
            extra={
                "error_type": error_type,
                "error_message": error_msg,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )


@router.get("/{project_id}/files")
async def list_project_files(project_id: int) -> Dict[str, Any]:
    """List files for a project.
    
    Args:
        project_id: Project ID
        
    Returns:
        List of files (metadata only, no content)
    """
    if not _has_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    with get_db() as db:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
        
        # Get files
        files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).order_by(ProjectFile.created_at.desc()).all()
        
        items = []
        for f in files:
            items.append({
                "id": f.id,
                "sha256": f.sha256,
                "size_bytes": f.size_bytes,
                "mime_type": f.mime_type,
                "original_filename": f.original_filename,  # Safe: only in DB, never logged
                "created_at": f.created_at.isoformat(),
            })
        
        return {
            "items": items,
            "total": len(items),
        }
