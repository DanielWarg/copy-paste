"""Autonomy Guard router - on-demand security checks."""
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Request

from app.core.logging import logger
from app.core.config import settings
from app.core.database import get_db
from app.core.privacy_guard import sanitize_for_logging, assert_no_content
from app.modules.autonomy_guard.checks import check_project, flag_project
from app.modules.projects.models import Project


router = APIRouter()


def _has_db() -> bool:
    """Check if database is available."""
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    return engine is not None and settings.database_url is not None


@router.get("/projects/{project_id}")
async def check_project_security(
    project_id: int,
    request: Request,
    auto_flag: bool = False,
) -> Dict[str, Any]:
    """Run autonomy checks for a project (on-demand).
    
    Args:
        project_id: Project ID
        request: FastAPI request (for request_id)
        auto_flag: If True, automatically create audit events for warnings/critical
        
    Returns:
        Check results with severity, message, why, checks
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
    
    # Run checks
    checks = check_project(project_id)
    
    # Determine overall severity
    severity = "ok"
    if checks:
        severities = [c.get("severity", "info") for c in checks]
        if "critical" in severities:
            severity = "critical"
        elif "warning" in severities:
            severity = "warning"
        else:
            severity = "info"
    
    # Auto-flag if requested and there are warnings/critical
    if auto_flag and checks:
        warnings_critical = [c for c in checks if c.get("severity") in ("warning", "critical")]
        if warnings_critical:
            request_id = getattr(request.state, "request_id", None)
            flag_project(project_id, warnings_critical, request_id=request_id)
    
    # Sanitize checks (ensure no content)
    sanitized_checks = []
    for check in checks:
        sanitized_check = sanitize_for_logging(check, context="audit")
        assert_no_content(sanitized_check, context="audit")
        sanitized_checks.append(sanitized_check)
    
    # Build response
    response = {
        "severity": severity,
        "message": f"Found {len(checks)} check(s)" if checks else "No issues found",
        "why": "Autonomy Guard checks completed",
        "checks": sanitized_checks,
    }
    
    # Log check run (privacy-safe)
    logger.info(
        "autonomy_guard_check_run",
        extra={
            "project_id": project_id,
            "checks_count": len(checks),
            "severity": severity,
        },
    )
    
    return response

