#!/usr/bin/env python3
"""
Integration test for audio ingestion -> scrub_v2 -> draft flow.

Tests:
- Audio upload -> event_id -> scrub_v2 -> draft generation
"""
import requests
import sys
import time
from datetime import datetime
import os

API_BASE = "http://localhost:8000"


def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)


def wait_for_server(url, timeout=10):
    """Waits for the server to be ready."""
    print(f"\nWaiting for server at {url}...")
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Server not responding!")
    return False


def create_test_audio_file():
    """Create a minimal test audio file (WAV format)."""
    # Create a minimal WAV file (silence, 1 second)
    # WAV header + 1 second of silence at 8kHz
    wav_header = b'RIFF' + (36 + 16000).to_bytes(4, 'little') + b'WAVE'
    wav_header += b'fmt ' + (16).to_bytes(4, 'little')  # fmt chunk size
    wav_header += (1).to_bytes(2, 'little')  # audio format (PCM)
    wav_header += (1).to_bytes(2, 'little')  # num channels
    wav_header += (8000).to_bytes(4, 'little')  # sample rate
    wav_header += (16000).to_bytes(4, 'little')  # byte rate
    wav_header += (2).to_bytes(2, 'little')  # block align
    wav_header += (16).to_bytes(2, 'little')  # bits per sample
    wav_header += b'data' + (16000).to_bytes(4, 'little')  # data chunk size
    wav_data = b'\x00' * 16000  # 1 second of silence
    
    test_file = '/tmp/test_audio.wav'
    with open(test_file, 'wb') as f:
        f.write(wav_header + wav_data)
    
    return test_file


def test_audio_ingest_flow():
    """Test: Audio upload -> event_id -> scrub_v2 -> draft generation"""
    print_section("TEST: Audio Ingest -> Scrub v2 -> Draft")
    
    try:
        # Create test audio file
        test_file = create_test_audio_file()
        print(f"✅ Created test audio file: {test_file}")
        
        # Step 1: Upload audio
        with open(test_file, 'rb') as f:
            files = {'file': ('test_audio.wav', f, 'audio/wav')}
            ingest_res = requests.post(
                f"{API_BASE}/api/v1/ingest/audio",
                files=files,
                timeout=60  # Transcription can take time
            )
        
        ingest_res.raise_for_status()
        ingest_data = ingest_res.json()
        event_id = ingest_data["event_id"]
        print(f"✅ Audio ingested: {event_id}")
        print(f"   Transcript meta: {ingest_data.get('transcript_meta', {})}")
        
        # Step 2: Scrub v2
        scrub_res = requests.post(
            f"{API_BASE}/api/v1/privacy/scrub_v2",
            json={
                "event_id": str(event_id),
                "production_mode": False,
                "max_retries": 2
            },
            timeout=30
        )
        scrub_res.raise_for_status()
        scrub_data = scrub_res.json()
        
        print(f"✅ Scrub v2 completed")
        print(f"   Verification passed: {scrub_data['verification_passed']}")
        print(f"   Approval required: {scrub_data['approval_required']}")
        
        # Step 3: Generate draft (with approval_token if needed)
        draft_res = requests.post(
            f"{API_BASE}/api/v1/draft/generate",
            json={
                "event_id": str(event_id),
                "clean_text": scrub_data['clean_text'],
                "production_mode": False,
                "approval_token": scrub_data.get('approval_token')
            },
            timeout=30
        )
        draft_res.raise_for_status()
        draft_data = draft_res.json()
        
        print(f"✅ Draft generated")
        print(f"   Text length: {len(draft_data['text'])}")
        print(f"   Citations: {len(draft_data['citations'])}")
        
        # Cleanup
        try:
            os.unlink(test_file)
        except:
            pass
        
        print("✅ Test PASSED: Audio ingest -> scrub_v2 -> draft flow works")
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("AUDIO INGESTION INTEGRATION TEST")
    print("="*60)
    print(f"Started: {datetime.now()}")

    if not wait_for_server(f"{API_BASE}/health"):
        sys.exit(1)

    result = test_audio_ingest_flow()

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    if result:
        print("✅ Audio ingestion test PASSED")
        sys.exit(0)
    else:
        print("❌ Audio ingestion test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

