#!/usr/bin/env python3
"""Integration test for Projects API with REAL data."""
import sys
import os
from pathlib import Path

# Set environment before imports
os.environ["SOURCE_SAFETY_MODE"] = "true"
os.environ["DEBUG"] = "true"

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from datetime import datetime
from app.core.config import settings
from app.core.database import init_db, get_db, engine
from app.modules.projects.models import Project, ProjectNote, ProjectFile, ProjectAuditEvent
from app.modules.transcripts.models import Transcript, TranscriptSegment


def setup_test_db():
    """Setup test database."""
    if not settings.database_url:
        print("⚠️  No DATABASE_URL set, skipping DB tests")
        return False
    
    try:
        init_db(settings.database_url)
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def test_create_project():
    """Test creating a project."""
    print("\n" + "=" * 60)
    print("TEST 1: Create Project")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        project = Project(
            name="Test Project",
            sensitivity="standard",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        assert project.id is not None, "Project should have ID"
        assert project.name == "Test Project", "Project name should match"
        print(f"✅ Created project ID: {project.id}")
        
        # Verify audit event created
        audit = db.query(ProjectAuditEvent).filter(
            ProjectAuditEvent.project_id == project.id,
            ProjectAuditEvent.action == "created",
        ).first()
        assert audit is not None, "Audit event should be created"
        assert "name" in audit.metadata_json, "Audit should contain name"
        assert "ip" not in audit.metadata_json, "Audit should not contain IP"
        print("✅ Audit event created and sanitized")
        
        # Cleanup
        db.delete(project)
        db.commit()
    
    return True


def test_list_projects():
    """Test listing projects."""
    print("\n" + "=" * 60)
    print("TEST 2: List Projects")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        # Create test projects
        projects = []
        for i in range(3):
            project = Project(
                name=f"Test Project {i}",
                sensitivity="standard" if i % 2 == 0 else "sensitive",
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(project)
            projects.append(project)
        db.commit()
        
        # List all
        all_projects = db.query(Project).all()
        assert len(all_projects) >= 3, "Should have at least 3 projects"
        print(f"✅ Found {len(all_projects)} projects")
        
        # Filter by sensitivity
        sensitive = db.query(Project).filter(Project.sensitivity == "sensitive").all()
        assert len(sensitive) >= 1, "Should have sensitive projects"
        print(f"✅ Filtered sensitive projects: {len(sensitive)}")
        
        # Cleanup
        for project in projects:
            db.delete(project)
        db.commit()
    
    return True


def test_project_audit():
    """Test project audit endpoint."""
    print("\n" + "=" * 60)
    print("TEST 3: Project Audit")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        # Create project
        project = Project(
            name="Audit Test Project",
            sensitivity="standard",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Create multiple audit events
        for i in range(3):
            audit = ProjectAuditEvent(
                project_id=project.id,
                action="test_action",
                severity="info",
                actor="test",
                created_at=datetime.utcnow(),
                metadata_json={"test": i},
            )
            db.add(audit)
        db.commit()
        
        # Get audit events
        audits = db.query(ProjectAuditEvent).filter(
            ProjectAuditEvent.project_id == project.id
        ).all()
        assert len(audits) >= 3, "Should have audit events"
        
        # Verify no forbidden fields
        for audit in audits:
            if audit.metadata_json:
                assert "ip" not in audit.metadata_json, "Audit should not contain IP"
                assert "filename" not in audit.metadata_json, "Audit should not contain filename"
                assert "user_agent" not in audit.metadata_json, "Audit should not contain user_agent"
        print("✅ Audit events retrieved and verified")
        
        # Cleanup
        db.delete(project)
        db.commit()
    
    return True


def test_integrity_verification():
    """Test integrity verification endpoint."""
    print("\n" + "=" * 60)
    print("TEST 4: Integrity Verification")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        # Create project with note
        project = Project(
            name="Integrity Test Project",
            sensitivity="standard",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        from app.core.privacy_guard import compute_integrity_hash
        
        note_text = "Test note content"
        note_hash = compute_integrity_hash(note_text)
        note = ProjectNote(
            project_id=project.id,
            title="Test Note",
            body_text=note_text,
            note_integrity_hash=note_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(note)
        db.commit()
        
        # Verify integrity
        from app.modules.projects.integrity import verify_project_integrity
        result = verify_project_integrity(project.id)
        assert result["integrity_ok"] is True, "Integrity should be OK"
        assert result["checked"]["notes"] == 1, "Should check 1 note"
        print("✅ Integrity verification passed")
        
        # Cleanup
        db.delete(note)
        db.delete(project)
        db.commit()
    
    return True


def test_autonomy_guard():
    """Test autonomy guard endpoint."""
    print("\n" + "=" * 60)
    print("TEST 5: Autonomy Guard")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        # Create sensitive project with file
        project = Project(
            name="Sensitive Test Project",
            sensitivity="sensitive",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        file = ProjectFile(
            project_id=project.id,
            original_filename="test.pdf",
            sha256="abc123",
            mime_type="application/pdf",
            size_bytes=1024,
            stored_encrypted=True,
            storage_path="abc123.bin",
            created_at=datetime.utcnow(),
        )
        db.add(file)
        db.commit()
        
        # Run autonomy checks
        from app.modules.autonomy_guard.checks import check_project
        checks = check_project(project.id)
        assert len(checks) > 0, "Should have checks"
        
        # Verify checks don't contain forbidden fields
        for check in checks:
            assert "ip" not in str(check), "Check should not contain IP"
            assert "filename" not in str(check), "Check should not contain filename"
        print(f"✅ Autonomy guard found {len(checks)} checks")
        
        # Cleanup
        db.delete(file)
        db.delete(project)
        db.commit()
    
    return True


def test_attach_transcripts():
    """Test attaching transcripts to project."""
    print("\n" + "=" * 60)
    print("TEST 6: Attach Transcripts")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        # Create project
        project = Project(
            name="Attach Test Project",
            sensitivity="standard",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Create transcripts
        transcripts = []
        for i in range(2):
            transcript = Transcript(
                title=f"Test Transcript {i}",
                source="test",
                language="sv",
                status="ready",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(transcript)
            transcripts.append(transcript)
        db.commit()
        
        # Attach transcripts
        for transcript in transcripts:
            transcript.project_id = project.id
        db.commit()
        
        # Verify attachment
        attached = db.query(Transcript).filter(Transcript.project_id == project.id).all()
        assert len(attached) == 2, "Should have 2 attached transcripts"
        print(f"✅ Attached {len(attached)} transcripts")
        
        # Cleanup
        for transcript in transcripts:
            db.delete(transcript)
        db.delete(project)
        db.commit()
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("PROJECTS API INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Setup
    db_available = setup_test_db()
    
    # Run tests
    tests = [
        test_create_project,
        test_list_projects,
        test_project_audit,
        test_integrity_verification,
        test_autonomy_guard,
        test_attach_transcripts,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

