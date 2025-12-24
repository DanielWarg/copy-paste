#!/usr/bin/env python3
"""Test script for Record purge (GDPR retention).

Creates test records, manipulates timestamps, and verifies purge behavior.

Usage:
    python scripts/test_purge.py [--dry-run] [--retention-days N]
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

BACKEND_URL = "http://localhost:8000"


def create_test_record() -> dict:
    """Create a test record via API."""
    print("Creating test record...")
    response = requests.post(
        f"{BACKEND_URL}/api/v1/record",
        json={
            "title": "Test Record for Purge",
            "sensitivity": "standard",
            "language": "sv",
        },
    )
    response.raise_for_status()
    record = response.json()
    print(f"✅ Created record: transcript_id={record['transcript_id']}")
    return record


def upload_test_audio(transcript_id: int) -> dict:
    """Upload test audio file."""
    print(f"Uploading test audio for transcript_id={transcript_id}...")
    
    # Create a minimal WAV file (44 bytes header + some data)
    wav_header = bytes([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # File size - 8
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # fmt chunk size
        0x01, 0x00,              # Audio format (PCM)
        0x01, 0x00,              # Num channels
        0x44, 0xAC, 0x00, 0x00,  # Sample rate
        0x88, 0x58, 0x01, 0x00,  # Byte rate
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x04, 0x00, 0x00, 0x00,  # Data chunk size
        0x00, 0x00, 0x00, 0x00,  # Sample data
    ])
    
    files = {"file": ("test.wav", wav_header, "audio/wav")}
    response = requests.post(
        f"{BACKEND_URL}/api/v1/record/{transcript_id}/audio",
        files=files,
    )
    response.raise_for_status()
    result = response.json()
    print(f"✅ Uploaded audio: file_id={result['file_id']}, sha256={result['sha256'][:16]}...")
    return result


def export_record(transcript_id: int) -> dict:
    """Export record to create export ZIP."""
    print(f"Exporting record transcript_id={transcript_id}...")
    response = requests.post(
        f"{BACKEND_URL}/api/v1/record/{transcript_id}/export",
        json={
            "confirm": True,
            "reason": "Test export for purge verification",
            "export_audio_mode": "encrypted",
        },
    )
    response.raise_for_status()
    result = response.json()
    print(f"✅ Exported: package_id={result['package_id']}, zip_path={result['zip_path']}")
    return result


def destroy_record(transcript_id: int) -> dict:
    """Destroy record (to create orphaned export ZIP)."""
    print(f"Destroying record transcript_id={transcript_id}...")
    response = requests.post(
        f"{BACKEND_URL}/api/v1/record/{transcript_id}/destroy",
        json={
            "dry_run": False,
            "confirm": True,
            "reason": "Test destruction for orphaned export verification",
        },
    )
    response.raise_for_status()
    result = response.json()
    print(f"✅ Destroyed: receipt_id={result['receipt_id']}")
    return result


def manipulate_timestamps(transcript_id: int, age_days: int) -> None:
    """Manipulate transcript created_at to simulate age.
    
    Note: This requires direct DB access. In production, you'd use a test DB.
    """
    print(f"⚠️  Cannot manipulate timestamps via API.")
    print(f"   In production, use test DB or set retention_days to 0 for immediate purge.")
    print(f"   For this test, we'll use --retention-days 0 to purge immediately.")


def run_purge(dry_run: bool = True, retention_days: int = 0) -> dict:
    """Run purge via Docker exec."""
    print(f"\nRunning purge (dry_run={dry_run}, retention_days={retention_days})...")
    
    cmd = [
        "docker-compose",
        "exec",
        "-T",
        "backend",
        "python",
        "-m",
        "app.modules.record.purge_runner",
    ]
    
    if dry_run:
        cmd.append("--dry-run")
    
    if retention_days is not None:
        cmd.extend(["--retention-days", str(retention_days)])
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"❌ Purge failed (exit code {result.returncode})")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return {}
    
    print(result.stdout)
    
    # Parse output (simple - just extract numbers)
    stats = {}
    for line in result.stdout.split("\n"):
        if "Purged records:" in line:
            stats["purged_count"] = int(line.split(":")[1].strip())
        elif "Files deleted:" in line:
            stats["files_deleted"] = int(line.split(":")[1].strip())
        elif "Exports deleted:" in line:
            stats["exports_deleted"] = int(line.split(":")[1].strip())
        elif "Errors:" in line:
            stats["errors"] = int(line.split(":")[1].strip())
    
    return stats


def verify_db_empty(transcript_id: int) -> bool:
    """Verify transcript is gone from DB."""
    print(f"Verifying transcript_id={transcript_id} is deleted...")
    response = requests.get(f"{BACKEND_URL}/api/v1/transcripts/{transcript_id}")
    if response.status_code == 404:
        print(f"✅ Transcript {transcript_id} not found (deleted)")
        return True
    elif response.status_code == 200:
        print(f"❌ Transcript {transcript_id} still exists")
        return False
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
        return False


def verify_export_deleted(zip_path: str) -> bool:
    """Verify export ZIP is deleted from disk."""
    print(f"Verifying export ZIP is deleted...")
    # Check via docker exec
    result = subprocess.run(
        [
            "docker-compose",
            "exec",
            "-T",
            "backend",
            "test",
            "!",
            "-f",
            zip_path,
        ],
        capture_output=True,
        check=False,
    )
    
    if result.returncode == 0:
        print(f"✅ Export ZIP deleted")
        return True
    else:
        print(f"❌ Export ZIP still exists")
        return False


def main() -> int:
    """Main test flow."""
    parser = argparse.ArgumentParser(description="Test Record purge")
    parser.add_argument("--dry-run", action="store_true", help="Only test dry-run mode")
    parser.add_argument("--retention-days", type=int, default=0, help="Retention days (0 = immediate)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Record Purge Test")
    print("=" * 60)
    
    try:
        # Step 1: Create test record
        record = create_test_record()
        transcript_id = record["transcript_id"]
        
        # Step 2: Upload audio
        upload_test_audio(transcript_id)
        
        # Step 3: Export (creates export ZIP)
        export_result = export_record(transcript_id)
        zip_path = export_result["zip_path"]
        
        # Step 4: Destroy record (creates orphaned export ZIP)
        destroy_record(transcript_id)
        
        # Step 5: Verify record is gone
        if not verify_db_empty(transcript_id):
            print("❌ Record should be deleted after destroy")
            return 1
        
        # Step 6: Run purge in dry-run mode
        print("\n" + "=" * 60)
        print("Step 6: Dry-run purge")
        print("=" * 60)
        dry_stats = run_purge(dry_run=True, retention_days=args.retention_days)
        
        if args.dry_run:
            print("\n✅ Dry-run test complete")
            return 0
        
        # Step 7: Run actual purge
        print("\n" + "=" * 60)
        print("Step 7: Actual purge")
        print("=" * 60)
        purge_stats = run_purge(dry_run=False, retention_days=args.retention_days)
        
        # Step 8: Verify export ZIP is deleted
        if not verify_export_deleted(zip_path):
            print("❌ Export ZIP should be deleted")
            return 1
        
        # Step 9: Run purge again (idempotency test)
        print("\n" + "=" * 60)
        print("Step 9: Idempotency test (run purge again)")
        print("=" * 60)
        idempotent_stats = run_purge(dry_run=False, retention_days=args.retention_days)
        
        if idempotent_stats.get("purged_count", 0) > 0:
            print("❌ Purge should be idempotent (no records purged on second run)")
            return 1
        
        print("\n" + "=" * 60)
        print("✅ All purge tests passed!")
        print("=" * 60)
        return 0
    
    except requests.exceptions.RequestException as e:
        print(f"❌ API error: {e}")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

