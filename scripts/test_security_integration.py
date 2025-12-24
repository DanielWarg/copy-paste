#!/usr/bin/env python3
"""Integration test for security modules with REAL data (DB + files).

Tests that security modules work in practice:
- Privacy Guard sanitizes audit events
- File encryption works
- Integrity verification works
- Source Safety Mode blocks identifiers
"""
import sys
import os
import tempfile
from pathlib import Path

# Set environment before imports
os.environ["SOURCE_SAFETY_MODE"] = "true"
os.environ["DEBUG"] = "true"  # Enable assertions

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from datetime import datetime
from app.core.config import settings
from app.core.database import init_db, get_db, engine
from app.core.privacy_guard import sanitize_for_logging, assert_no_content, compute_integrity_hash
from app.modules.transcripts.models import Transcript, TranscriptSegment, TranscriptAuditEvent
from app.modules.projects.models import Project, ProjectNote, ProjectFile, ProjectAuditEvent
from app.modules.projects.file_storage import store_file, retrieve_file, compute_file_hash, generate_encryption_key
from app.modules.projects.integrity import verify_project_integrity
from app.modules.autonomy_guard.checks import check_project, flag_project


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


def test_privacy_guard_audit_events():
    """Test that audit events are sanitized."""
    print("\n" + "=" * 60)
    print("TEST 1: Privacy Guard in Audit Events")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    # Create transcript with audit event
    with get_db() as db:
        transcript = Transcript(
            title="Test Transcript",
            source="test",
            language="sv",
            status="ready",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        # Try to create audit event with forbidden fields
        forbidden_metadata = {
            "ip": "192.168.1.1",  # Should be blocked
            "filename": "test.pdf",  # Should be blocked
            "transcript_text": "This is forbidden content",  # Should be blocked
            "count": 1,  # Should pass
        }
        
        # Sanitize metadata
        try:
            sanitized = sanitize_for_logging(forbidden_metadata, context="audit")
            print("❌ Should have raised AssertionError in DEV mode")
            return False
        except AssertionError:
            print("✅ Privacy Guard correctly blocks forbidden fields in DEV mode")
        
        # Create audit event with safe metadata
        safe_metadata = sanitize_for_logging({"count": 1, "format": "srt"}, context="audit")
        assert_no_content(safe_metadata, context="audit")
        
        audit = TranscriptAuditEvent(
            transcript_id=transcript.id,
            action="exported",
            actor="system",
            created_at=datetime.utcnow(),
            metadata_json=safe_metadata,
        )
        db.add(audit)
        db.commit()
        
        # Verify audit event was saved
        saved_audit = db.query(TranscriptAuditEvent).filter(
            TranscriptAuditEvent.transcript_id == transcript.id
        ).first()
        
        assert saved_audit is not None, "Audit event should be saved"
        assert "count" in saved_audit.metadata_json, "Safe fields should be saved"
        assert "ip" not in saved_audit.metadata_json, "Forbidden fields should not be saved"
        assert "filename" not in saved_audit.metadata_json, "Forbidden fields should not be saved"
        assert "transcript_text" not in saved_audit.metadata_json, "Forbidden fields should not be saved"
        
        print("✅ Audit events correctly sanitized and saved")
        
        # Cleanup
        db.delete(transcript)
        db.commit()
    
    return True


def test_file_encryption():
    """Test file encryption with real files."""
    print("\n" + "=" * 60)
    print("TEST 2: File Encryption")
    print("=" * 60)
    
    # Check if PROJECT_FILES_KEY is set
    if not os.getenv("PROJECT_FILES_KEY"):
        print("⚠️  PROJECT_FILES_KEY not set, generating test key...")
        test_key = generate_encryption_key()
        os.environ["PROJECT_FILES_KEY"] = test_key
        print(f"✅ Generated test key: {test_key[:20]}...")
    
    # Create test file content
    test_content = b"This is test file content for encryption testing"
    sha256 = compute_file_hash(test_content)
    
    try:
        # Store encrypted file
        storage_path = store_file(test_content, sha256)
        print(f"✅ File stored encrypted: {storage_path}")
        
        # Retrieve and decrypt
        retrieved_content = retrieve_file(sha256)
        assert retrieved_content == test_content, "Decrypted content should match original"
        print("✅ File retrieved and decrypted correctly")
        
        # Verify hash
        retrieved_hash = compute_file_hash(retrieved_content)
        assert retrieved_hash == sha256, "Hash should match"
        print("✅ File integrity verified")
        
        return True
    except Exception as e:
        print(f"❌ File encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrity_verification():
    """Test integrity verification with real data."""
    print("\n" + "=" * 60)
    print("TEST 3: Integrity Verification")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        # Create project
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
        
        # Create note with integrity hash
        note_text = "This is a test note"
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
        result = verify_project_integrity(project.id)
        assert result["integrity_ok"] is True, "Integrity should be OK"
        assert result["checked"]["notes"] == 1, "Should check 1 note"
        assert len(result["issues"]) == 0, "Should have no issues"
        print("✅ Integrity verification passed")
        
        # Test integrity failure (corrupt note)
        note.body_text = "Corrupted content"
        db.commit()
        
        result = verify_project_integrity(project.id)
        assert result["integrity_ok"] is False, "Integrity should fail"
        assert len(result["issues"]) > 0, "Should have issues"
        print("✅ Integrity failure detection works")
        
        # Cleanup
        db.delete(note)
        db.delete(project)
        db.commit()
    
    return True


def test_autonomy_guard():
    """Test autonomy guard with real data."""
    print("\n" + "=" * 60)
    print("TEST 4: Autonomy Guard")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    with get_db() as db:
        # Create sensitive project
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
        
        # Create file (should trigger warning)
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
        checks = check_project(project.id)
        assert len(checks) > 0, "Should have checks"
        
        # Find sensitive project check
        sensitive_check = next((c for c in checks if "känsligt" in c["message"].lower()), None)
        assert sensitive_check is not None, "Should flag sensitive project with files"
        print(f"✅ Autonomy guard flagged: {sensitive_check['message']}")
        
        # Flag project (create audit events)
        flag_project(project.id, checks, request_id="test-123")
        
        # Verify audit events created
        audit_events = db.query(ProjectAuditEvent).filter(
            ProjectAuditEvent.project_id == project.id,
            ProjectAuditEvent.action == "system_flag",
        ).all()
        assert len(audit_events) > 0, "Should have audit events"
        
        # Verify audit events don't contain content
        for audit in audit_events:
            if audit.metadata_json:
                assert_no_content(audit.metadata_json, context="audit")
        print("✅ Audit events created without content")
        
        # Cleanup
        db.delete(file)
        db.delete(project)
        db.commit()
    
    return True


def test_source_safety_mode_enforcement():
    """Test that Source Safety Mode is enforced."""
    print("\n" + "=" * 60)
    print("TEST 5: Source Safety Mode Enforcement")
    print("=" * 60)
    
    # Verify SOURCE_SAFETY_MODE is enabled
    assert settings.source_safety_mode is True, "SOURCE_SAFETY_MODE should be True"
    print("✅ SOURCE_SAFETY_MODE is enabled")
    
    # Test that source identifiers are blocked
    test_data = {
        "action": "file_uploaded",
        "ip": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "filename": "source.pdf",
        "count": 1,
    }
    
    try:
        sanitize_for_logging(test_data, context="test")
        print("❌ Should have raised AssertionError")
        return False
    except AssertionError:
        print("✅ Source identifiers correctly blocked")
    
    return True


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("SECURITY MODULES INTEGRATION TEST")
    print("=" * 60)
    print()
    print(f"DEBUG: {settings.debug}")
    print(f"SOURCE_SAFETY_MODE: {settings.source_safety_mode}")
    print(f"DATABASE_URL: {'Set' if settings.database_url else 'Not set'}")
    print()
    
    # Setup
    db_available = setup_test_db()
    
    # Run tests
    tests = [
        test_source_safety_mode_enforcement,  # Always runs (no DB needed)
        test_privacy_guard_audit_events,  # Needs DB
        test_file_encryption,  # Needs PROJECT_FILES_KEY
        test_integrity_verification,  # Needs DB
        test_autonomy_guard,  # Needs DB
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
        print("✅ All integration tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

