"""Rule-based autonomy checks - NO AI, deterministic rules."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.core.database import get_db
from app.core.config import settings
from app.core.privacy_guard import sanitize_for_logging, assert_no_content
from app.modules.projects.models import Project, ProjectNote, ProjectFile, ProjectAuditEvent
from app.modules.transcripts.models import Transcript, TranscriptSegment


def check_project(project_id: int) -> List[Dict[str, Any]]:
    """Run all autonomy checks for a project.
    
    Returns:
        List of check results (severity, message, why)
    """
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    if not engine:
        return []  # No DB mode
    
    results: List[Dict[str, Any]] = []
    
    with get_db() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return results
        
        # Check 1: Unusually short transcript
        transcripts = db.query(Transcript).filter(Transcript.project_id == project_id).all()
        for transcript in transcripts:
            segments = db.query(TranscriptSegment).filter(
                TranscriptSegment.transcript_id == transcript.id
            ).all()
            total_chars = sum(len(s.text) for s in segments)
            if total_chars < 100:  # Threshold: 100 chars
                results.append({
                    "severity": "warning",
                    "message": f"Transcript '{transcript.title}' är ovanligt kort ({total_chars} tecken).",
                    "why": "Korta transkriptioner kan tyda på ofullständig data eller tekniskt fel.",
                })
        
        # Check 2: Low average confidence
        for transcript in transcripts:
            segments = db.query(TranscriptSegment).filter(
                TranscriptSegment.transcript_id == transcript.id
            ).filter(TranscriptSegment.confidence.isnot(None)).all()
            if segments:
                avg_confidence = sum(s.confidence for s in segments) / len(segments)
                if avg_confidence < 0.7:  # Threshold: 70%
                    results.append({
                        "severity": "warning",
                        "message": f"Transcript '{transcript.title}' har låg genomsnittlig konfidens ({avg_confidence:.1%}).",
                        "why": "Låg konfidens kan tyda på dålig ljudkvalitet eller transkriptionsfel.",
                    })
        
        # Check 3: Rapid deletion activity
        recent_deletions = db.query(ProjectAuditEvent).filter(
            ProjectAuditEvent.project_id == project_id,
            ProjectAuditEvent.action == "destroyed",
            ProjectAuditEvent.created_at >= datetime.utcnow() - timedelta(hours=1),
        ).count()
        if recent_deletions > 3:  # Threshold: 3 deletions in 1 hour
            results.append({
                "severity": "warning",
                "message": f"Ovanligt många raderingar ({recent_deletions}) under senaste timmen.",
                "why": "Rapid deletion activity kan tyda på misstag eller säkerhetsproblem.",
            })
        
        # Check 4: Sensitive project with retained files
        if project.sensitivity == "sensitive":
            files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).count()
            if files > 0:
                results.append({
                    "severity": "warning",
                    "message": "Detta projekt innehåller känsligt material som fortfarande sparas.",
                    "why": "Projektet är markerat som känsligt och filer är kvar. Överväg att arkivera eller radera när arbetet är klart.",
                })
        
        # Check 5: Inactive project with content
        if project.status == "archived":
            notes_count = db.query(ProjectNote).filter(ProjectNote.project_id == project_id).count()
            files_count = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).count()
            transcripts_count = len(transcripts)
            total_content = notes_count + files_count + transcripts_count
            if total_content > 0:
                last_activity = project.updated_at
                days_inactive = (datetime.utcnow() - last_activity).days
                if days_inactive > 90:  # Threshold: 90 days
                    results.append({
                        "severity": "info",
                        "message": f"Arkiverat projekt med innehåll ({total_content} artefakter) har varit inaktivt i {days_inactive} dagar.",
                        "why": "Överväg att radera innehåll om det inte längre behövs.",
                    })
    
    return results


def flag_project(project_id: int, checks: List[Dict[str, Any]], request_id: Optional[str] = None) -> None:
    """Create audit event for autonomy guard flags.
    
    Args:
        project_id: Project ID
        checks: List of check results
        request_id: Optional request ID
    """
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    if not engine or not checks:
        return
    
    with get_db() as db:
        for check in checks:
            # Sanitize metadata (ensure no content)
            metadata = sanitize_for_logging({
                "message": check["message"],
                "why": check["why"],
            }, context="audit")
            assert_no_content(metadata, context="audit")
            
            audit = ProjectAuditEvent(
                project_id=project_id,
                action="system_flag",
                severity=check["severity"],
                actor="autonomy_guard",
                request_id=request_id,
                created_at=datetime.utcnow(),
                metadata_json=metadata,
            )
            db.add(audit)
        db.commit()

