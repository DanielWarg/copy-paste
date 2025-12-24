#!/usr/bin/env python3
"""Retention cleanup script - removes old files and projects according to policy."""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.database import get_db, engine
from app.core.logging import logger
from app.core.privacy_guard import sanitize_for_logging
from app.modules.projects.models import Project, ProjectFile, ProjectAuditEvent
from app.modules.projects.file_storage import delete_file, _ensure_storage_dir


def cleanup_retention() -> dict:
    """Run retention cleanup according to policy.
    
    Returns:
        Dict with cleanup counts and status
    """
    if not engine:
        logger.warning("cleanup_retention_no_db", extra={"message": "Database not available, skipping cleanup"})
        return {"status": "skipped", "reason": "no_database"}
    
    counts = {
        "temp_files_deleted": 0,
        "destroyed_projects_deleted": 0,
        "sensitive_projects_deleted": 0,
        "errors": 0,
    }
    
    try:
        with get_db() as db:
            now = datetime.utcnow()
            
            # 1. Cleanup temp files older than TTL
            temp_ttl = timedelta(hours=settings.temp_file_ttl_hours)
            temp_cutoff = now - temp_ttl
            
            # Find files marked as temp (we'd need a temp flag in ProjectFile model)
            # For now, we'll clean up files from destroyed projects
            destroyed_projects = db.query(Project).filter(
                Project.status == "destroyed",
                Project.updated_at < temp_cutoff,
            ).all()
            
            for project in destroyed_projects:
                files = db.query(ProjectFile).filter(ProjectFile.project_id == project.id).all()
                for file in files:
                    try:
                        delete_file(file.sha256)
                        counts["temp_files_deleted"] += 1
                    except Exception as e:
                        logger.error(
                            "cleanup_file_error",
                            extra=sanitize_for_logging({
                                "file_id": file.id,
                                "sha256": file.sha256[:8],  # Only first 8 chars
                                "error": str(e),
                            }, context="audit"),
                        )
                        counts["errors"] += 1
            
            # 2. Cleanup destroyed projects older than retention
            default_retention = timedelta(days=settings.retention_days_default)
            default_cutoff = now - default_retention
            
            destroyed_projects_old = db.query(Project).filter(
                Project.status == "destroyed",
                Project.updated_at < default_cutoff,
            ).all()
            
            for project in destroyed_projects_old:
                if project.sensitivity == "sensitive":
                    # Sensitive projects have shorter retention
                    sensitive_retention = timedelta(days=settings.retention_days_sensitive)
                    sensitive_cutoff = now - sensitive_retention
                    if project.updated_at >= sensitive_cutoff:
                        continue  # Not old enough yet
                    counts["sensitive_projects_deleted"] += 1
                else:
                    counts["destroyed_projects_deleted"] += 1
                
                # Hard delete project (CASCADE will delete related records)
                db.delete(project)
            
            db.commit()
            
            # 3. Create audit event for cleanup run
            if counts["temp_files_deleted"] > 0 or counts["destroyed_projects_deleted"] > 0:
                # Find a project to attach audit to (or create system project)
                # For now, we'll create a system audit event
                # In a real system, you might have a "system" project
                audit = ProjectAuditEvent(
                    project_id=1,  # Placeholder - in real system, use system project ID
                    action="system_cleanup_run",
                    severity="info",
                    actor="system",
                    created_at=now,
                    metadata_json=sanitize_for_logging({
                        "temp_files_deleted": counts["temp_files_deleted"],
                        "destroyed_projects_deleted": counts["destroyed_projects_deleted"],
                        "sensitive_projects_deleted": counts["sensitive_projects_deleted"],
                        "errors": counts["errors"],
                    }, context="audit"),
                )
                db.add(audit)
                db.commit()
            
            logger.info(
                "cleanup_retention_complete",
                extra=sanitize_for_logging({
                    "temp_files_deleted": counts["temp_files_deleted"],
                    "destroyed_projects_deleted": counts["destroyed_projects_deleted"],
                    "sensitive_projects_deleted": counts["sensitive_projects_deleted"],
                    "errors": counts["errors"],
                }, context="audit"),
            )
            
            return {
                "status": "success",
                "counts": counts,
            }
    
    except Exception as e:
        logger.error(
            "cleanup_retention_error",
            extra=sanitize_for_logging({
                "error": str(e),
            }, context="audit"),
        )
        return {
            "status": "error",
            "error": str(e),
            "counts": counts,
        }


if __name__ == "__main__":
    print("Running retention cleanup...")
    result = cleanup_retention()
    print(f"Status: {result['status']}")
    if "counts" in result:
        print(f"Counts: {result['counts']}")
    if result["status"] == "error":
        sys.exit(1)

