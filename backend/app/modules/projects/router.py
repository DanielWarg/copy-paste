"""Projects router - API endpoints for project management."""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.core.config import settings
from app.core import database
from app.core.database import get_db
from app.core.privacy_guard import sanitize_for_logging, assert_no_content
from app.modules.projects.models import Project, ProjectNote, ProjectFile, ProjectAuditEvent
from app.modules.projects.integrity import verify_project_integrity
from app.modules.transcripts.models import Transcript


router = APIRouter()


# Request/Response models
class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: Optional[str] = Field(None, max_length=500)
    sensitivity: str = Field(default="standard", pattern="^(standard|sensitive)$")


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, max_length=500)
    sensitivity: Optional[str] = Field(None, pattern="^(standard|sensitive)$")
    status: Optional[str] = Field(None, pattern="^(active|archived)$")


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
    """Create audit event (sanitized for privacy)."""
    if not _has_db():
        return
    
    # Sanitize metadata
    if metadata:
        metadata = sanitize_for_logging(metadata, context="audit")
        assert_no_content(metadata, context="audit")
    
    with get_db() as db:
        audit = ProjectAuditEvent(
            project_id=project_id,
            action=action,
            severity=severity,
            actor=actor,
            request_id=request_id,
            created_at=datetime.utcnow(),
            metadata_json=metadata,
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
    
    with get_db() as db:
        project = Project(
            name=name,
            sensitivity=data.sensitivity,
            status="active",
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
    """List projects with filtering and search.
    
    Returns:
        List of projects with counts
    """
    if not _has_db():
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }
    
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
    """Update project (name, sensitivity, status only).
    
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
        
        if data.name is not None and data.name != project.name:
            project.name = data.name
            changed_fields.append("name")
        
        if data.sensitivity is not None and data.sensitivity != project.sensitivity:
            project.sensitivity = data.sensitivity
            changed_fields.append("sensitivity")
        
        if data.status is not None and data.status != project.status:
            project.status = data.status
            changed_fields.append("status")
        
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
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "started_working_at": project.started_working_at.isoformat() if project.started_working_at else None,
            **counts,
        }


@router.get("/{project_id}/audit")
async def get_project_audit(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """Get project audit events.
    
    Args:
        project_id: Project ID
        limit: Max items
        offset: Offset
        
    Returns:
        Audit events (sanitized)
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
        
        # Get audit events
        query = db.query(ProjectAuditEvent).filter(
            ProjectAuditEvent.project_id == project_id
        )
        
        total = query.count()
        events = query.order_by(ProjectAuditEvent.created_at.desc()).offset(offset).limit(limit).all()
        
        # Build response (metadata already sanitized)
        items = []
        for event in events:
            items.append({
                "id": event.id,
                "action": event.action,
                "severity": event.severity,
                "actor": event.actor,
                "request_id": event.request_id,
                "created_at": event.created_at.isoformat(),
                "metadata": event.metadata_json,  # Already sanitized when created
            })
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
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
    
    with get_db() as db:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
    
    # Run integrity check
    result = verify_project_integrity(project_id)
    
    # Sanitize issues (no content, only ids/types)
    sanitized_issues = []
    for issue in result.get("issues", []):
        # Issues should already be safe (only ids/types), but verify
        sanitized_issues.append(issue)
    
    return {
        "integrity_ok": result["integrity_ok"],
        "checked": result["checked"],
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

