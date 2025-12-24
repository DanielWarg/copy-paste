#!/usr/bin/env python3
"""Integration test for Record API with REAL data."""
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
from app.modules.record import service
from app.modules.record.models import AudioAsset
from app.modules.projects.models import Project
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


def create_test_audio_file() -> bytes:
    """Create a small test audio file (fake WAV header)."""
    # Minimal WAV header + some fake data
    wav_header = b'RIFF' + (1000).to_bytes(4, 'little') + b'WAVE' + b'fmt ' + (16).to_bytes(4, 'little')
    wav_header += (1).to_bytes(2, 'little')  # PCM
    wav_header += (1).to_bytes(2, 'little')  # Mono
    wav_header += (44100).to_bytes(4, 'little')  # Sample rate
    wav_header += (88200).to_bytes(4, 'little')  # Byte rate
    wav_header += (2).to_bytes(2, 'little')  # Block align
    wav_header += (16).to_bytes(2, 'little')  # Bits per sample
    wav_header += b'data' + (100).to_bytes(4, 'little')
    wav_header += b'\x00' * 100  # Fake audio data
    return wav_header


def test_create_record():
    """Test creating a record (project + transcript)."""
    print("\n" + "=" * 60)
    print("TEST 1: Create Record")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    try:
        # Create record with auto project
        result = service.create_record_project(
            project_id=None,
            title="Test Recording",
            sensitivity="standard",
            language="sv",
        )
        
        assert "project_id" in result, "Should have project_id"
        assert "transcript_id" in result, "Should have transcript_id"
        assert result["title"] == "Test Recording", "Title should match"
        print(f"✅ Created record: project_id={result['project_id']}, transcript_id={result['transcript_id']}")
        
        # Verify project created
        with get_db() as db:
            project = db.query(Project).filter(Project.id == result["project_id"]).first()
            assert project is not None, "Project should exist"
            assert project.sensitivity == "standard", "Sensitivity should match"
        
        # Verify transcript created
        with get_db() as db:
            transcript = db.query(Transcript).filter(Transcript.id == result["transcript_id"]).first()
            assert transcript is not None, "Transcript should exist"
            assert transcript.status == "uploaded", "Status should be uploaded"
        
        # Cleanup
        with get_db() as db:
            db.query(Transcript).filter(Transcript.id == result["transcript_id"]).delete()
            db.query(Project).filter(Project.id == result["project_id"]).delete()
            db.commit()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_upload_audio():
    """Test uploading audio file."""
    print("\n" + "=" * 60)
    print("TEST 2: Upload Audio")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    try:
        # Create record first
        record = service.create_record_project(
            project_id=None,
            title="Audio Test",
            sensitivity="standard",
        )
        transcript_id = record["transcript_id"]
        
        # Create test audio file
        audio_content = create_test_audio_file()
        
        # Upload audio
        result = service.upload_audio(
            transcript_id=transcript_id,
            file_content=audio_content,
            mime_type="audio/wav",
        )
        
        assert result["status"] == "ok", "Status should be ok"
        assert "sha256" in result, "Should have sha256"
        assert result["size_bytes"] > 0, "Size should be > 0"
        assert result["mime_type"] == "audio/wav", "MIME type should match"
        print(f"✅ Uploaded audio: file_id={result['file_id']}, sha256={result['sha256'][:16]}...")
        
        # Verify audio asset created
        with get_db() as db:
            audio_asset = db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).first()
            assert audio_asset is not None, "Audio asset should exist"
            assert audio_asset.sha256 == result["sha256"], "SHA256 should match"
        
        # Cleanup
        with get_db() as db:
            db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).delete()
            db.query(Transcript).filter(Transcript.id == transcript_id).delete()
            db.query(Project).filter(Project.id == record["project_id"]).delete()
            db.commit()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_record():
    """Test exporting record package (default encrypted)."""
    print("\n" + "=" * 60)
    print("TEST 3: Export Record (Default Encrypted)")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    # Check if PROJECT_FILES_KEY is set
    if not os.getenv("PROJECT_FILES_KEY"):
        print("⚠️  PROJECT_FILES_KEY not set, skipping export test")
        return True
    
    try:
        # Create record and upload audio
        record = service.create_record_project(title="Export Test")
        transcript_id = record["transcript_id"]
        
        audio_content = create_test_audio_file()
        service.upload_audio(transcript_id, audio_content, "audio/wav")
        
        # Export package (default: encrypted)
        result = service.export_record_package(
            transcript_id=transcript_id,
            confirm=True,
            reason="Test export",
            export_audio_mode="encrypted",
        )
        
        assert result["status"] == "ok", "Status should be ok"
        assert "package_id" in result, "Should have package_id"
        assert "receipt_id" in result, "Should have receipt_id"
        assert result["audio_mode"] == "encrypted", "Should be encrypted by default"
        assert len(result.get("warnings", [])) == 0, "Should have no warnings for encrypted"
        print(f"✅ Exported package: package_id={result['package_id']}, audio_mode={result['audio_mode']}")
        
        # Verify zip file exists and contains manifest
        if "zip_path" in result:
            assert os.path.exists(result["zip_path"]), "Zip file should exist"
            
            # Check manifest exists in zip
            import zipfile
            with zipfile.ZipFile(result["zip_path"], "r") as zip_file:
                file_list = zip_file.namelist()
                assert "manifest.json" in file_list, "Should contain manifest.json"
                assert "audio.bin" in file_list, "Should contain audio.bin (encrypted)"
                assert "audio.dec" not in file_list, "Should NOT contain audio.dec"
                
                # Read manifest
                manifest_data = json.loads(zip_file.read("manifest.json"))
                assert manifest_data["audio_mode"] == "encrypted", "Manifest should show encrypted"
                assert "integrity_hashes" in manifest_data, "Manifest should have integrity_hashes"
                print(f"✅ Manifest verified: audio_mode={manifest_data['audio_mode']}")
            
            # Cleanup zip
            os.unlink(result["zip_path"])
        
        # Cleanup
        with get_db() as db:
            db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).delete()
            db.query(Transcript).filter(Transcript.id == transcript_id).delete()
            db.query(Project).filter(Project.id == record["project_id"]).delete()
            db.commit()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_destroy_record_dry_run():
    """Test destroy record (dry run)."""
    print("\n" + "=" * 60)
    print("TEST 4: Destroy Record (Dry Run)")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    try:
        # Create record and upload audio
        record = service.create_record_project(title="Destroy Test")
        transcript_id = record["transcript_id"]
        
        audio_content = create_test_audio_file()
        service.upload_audio(transcript_id, audio_content, "audio/wav")
        
        # Dry run destroy
        result = service.destroy_record(
            transcript_id=transcript_id,
            dry_run=True,
            confirm=False,
            reason=None,
        )
        
        assert result["status"] == "dry_run", "Status should be dry_run"
        assert "would_delete" in result, "Should have would_delete"
        assert result["would_delete"]["files"] == 1, "Should have 1 file"
        print(f"✅ Dry run: would delete {result['would_delete']}")
        
        # Verify nothing was deleted
        with get_db() as db:
            transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
            assert transcript is not None, "Transcript should still exist"
        
        # Cleanup
        with get_db() as db:
            db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).delete()
            db.query(Transcript).filter(Transcript.id == transcript_id).delete()
            db.query(Project).filter(Project.id == record["project_id"]).delete()
            db.commit()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_destroy_record_confirm():
    """Test destroy record (confirm)."""
    print("\n" + "=" * 60)
    print("TEST 5: Destroy Record (Confirm)")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    try:
        # Create record and upload audio
        record = service.create_record_project(title="Destroy Confirm Test")
        transcript_id = record["transcript_id"]
        
        audio_content = create_test_audio_file()
        service.upload_audio(transcript_id, audio_content, "audio/wav")
        
        # Confirm destroy
        result = service.destroy_record(
            transcript_id=transcript_id,
            dry_run=False,
            confirm=True,
            reason="Test destruction",
        )
        
        assert result["status"] == "destroyed", "Status should be destroyed"
        assert "receipt_id" in result, "Should have receipt_id"
        assert "destroyed_at" in result, "Should have destroyed_at"
        assert result["counts"]["files"] == 1, "Should have deleted 1 file"
        print(f"✅ Destroyed: receipt_id={result['receipt_id']}")
        
        # Verify everything was deleted
        with get_db() as db:
            transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
            assert transcript is None, "Transcript should be deleted"
            
            audio_asset = db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).first()
            assert audio_asset is None, "Audio asset should be deleted"
        
        # Cleanup project
        with get_db() as db:
            db.query(Project).filter(Project.id == record["project_id"]).delete()
            db.commit()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_privacy_guard():
    """Test that audit events don't contain forbidden fields."""
    print("\n" + "=" * 60)
    print("TEST 6: Privacy Guard")
    print("=" * 60)
    
    if not engine:
        print("⚠️  Skipping (no DB)")
        return True
    
    try:
        # Create record
        record = service.create_record_project(title="Privacy Test")
        transcript_id = record["transcript_id"]
        
        # Upload audio
        audio_content = create_test_audio_file()
        service.upload_audio(transcript_id, audio_content, "audio/wav")
        
        # Check audit events
        with get_db() as db:
            from app.modules.transcripts.models import TranscriptAuditEvent
            audits = db.query(TranscriptAuditEvent).filter(
                TranscriptAuditEvent.transcript_id == transcript_id
            ).all()
            
            for audit in audits:
                if audit.metadata_json:
                    # Verify no forbidden fields
                    assert "ip" not in str(audit.metadata_json), "Should not contain IP"
                    assert "filename" not in str(audit.metadata_json), "Should not contain filename"
                    assert "user_agent" not in str(audit.metadata_json), "Should not contain user_agent"
                    assert "url" not in str(audit.metadata_json), "Should not contain URL"
        
        print("✅ Audit events are privacy-safe")
        
        # Cleanup
        with get_db() as db:
            db.query(AudioAsset).filter(AudioAsset.transcript_id == transcript_id).delete()
            db.query(Transcript).filter(Transcript.id == transcript_id).delete()
            db.query(Project).filter(Project.id == record["project_id"]).delete()
            db.commit()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("RECORD API INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Setup
    db_available = setup_test_db()
    
    # Run tests
    tests = [
        test_create_record,
        test_upload_audio,
        test_export_record,
        test_destroy_record_dry_run,
        test_destroy_record_confirm,
        test_destroy_record_resume,
        test_privacy_guard,
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

