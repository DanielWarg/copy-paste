"""Integrity verification for projects."""
from typing import Dict, List, Any

from app.core.database import get_db
from app.core.config import settings
from app.modules.projects.models import Project, ProjectNote, ProjectFile
from app.modules.transcripts.models import Transcript, TranscriptSegment
from app.core.privacy_guard import compute_integrity_hash, verify_integrity


def verify_project_integrity(project_id: int) -> Dict[str, Any]:
    """Verify integrity of all artifacts in a project.
    
    Args:
        project_id: Project ID
        
    Returns:
        Dict with integrity_ok, checked counts, and issues list
    """
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    if not engine:
        # No DB mode - return mock
        return {
            "integrity_ok": True,
            "checked": {"transcripts": 0, "notes": 0, "files": 0},
            "issues": [],
        }
    
    issues: List[str] = []
    checked = {"transcripts": 0, "notes": 0, "files": 0}
    
    with get_db() as db:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "integrity_ok": False,
                "checked": checked,
                "issues": [f"Project {project_id} not found"],
            }
        
        # Verify notes
        notes = db.query(ProjectNote).filter(ProjectNote.project_id == project_id).all()
        for note in notes:
            checked["notes"] += 1
            expected_hash = note.note_integrity_hash
            actual_hash = compute_integrity_hash(note.body_text)
            if actual_hash != expected_hash:
                issues.append(f"Note {note.id}: integrity hash mismatch")
        
        # Verify transcripts (if raw_integrity_hash is set)
        transcripts = db.query(Transcript).filter(Transcript.project_id == project_id).all()
        for transcript in transcripts:
            checked["transcripts"] += 1
            if transcript.raw_integrity_hash:
                # Recompute hash from segments
                segments = db.query(TranscriptSegment).filter(
                    TranscriptSegment.transcript_id == transcript.id
                ).order_by(TranscriptSegment.start_ms).all()
                raw_content = "\n".join(s.text for s in segments)
                actual_hash = compute_integrity_hash(raw_content)
                if actual_hash != transcript.raw_integrity_hash:
                    issues.append(f"Transcript {transcript.id}: integrity hash mismatch")
        
        # Verify files (check file exists on disk)
        files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
        for file in files:
            checked["files"] += 1
            # Check file exists (actual file verification would require decryption)
            from app.modules.projects.file_storage import _ensure_storage_dir
            storage_dir = _ensure_storage_dir()
            storage_path = storage_dir / f"{file.sha256}.bin"
            if not storage_path.exists():
                issues.append(f"File {file.id}: storage file missing")
    
    return {
        "integrity_ok": len(issues) == 0,
        "checked": checked,
        "issues": issues,
    }

