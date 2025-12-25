#!/usr/bin/env python3
"""Test upload directly."""
import json
import subprocess

# Create record
result = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'http://localhost:8000/api/v1/record/create',
     '-H', 'Content-Type: application/json',
     '-H', 'X-Request-Id: test-upload-direct',
     '-d', '{"title": "Upload Direct Test", "sensitivity": "standard"}'],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
transcript_id = data['transcript_id']
print(f"Created transcript_id: {transcript_id}")

# Upload file
upload_result = subprocess.run(
    ['curl', '-s', '-X', 'POST', f'http://localhost:8000/api/v1/record/{transcript_id}/audio',
     '-H', 'X-Request-Id: test-upload-direct-2',
     '-F', 'file=@Del21.wav'],
    capture_output=True, text=True
)
print(f"Upload status: {upload_result.returncode}")
print(f"Upload response: {upload_result.stdout}")

