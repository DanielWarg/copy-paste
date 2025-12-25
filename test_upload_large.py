#!/usr/bin/env python3
"""Test large file upload."""
import json
import subprocess
import sys

# Create record
result = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'http://localhost:8000/api/v1/record/create',
     '-H', 'Content-Type: application/json',
     '-H', 'X-Request-Id: test-large-upload-py',
     '-d', '{"title": "Large Upload Test", "sensitivity": "standard"}'],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
transcript_id = data['transcript_id']
print(f"Created transcript_id: {transcript_id}")

# Upload file with timeout
print("Uploading Del21.wav (20MB)...")
upload_result = subprocess.run(
    ['curl', '-s', '-X', 'POST', f'http://localhost:8000/api/v1/record/{transcript_id}/audio',
     '-H', 'X-Request-Id: test-large-upload-py-2',
     '-F', 'file=@Del21.wav',
     '--max-time', '120'],
    capture_output=True, text=True
)
print(f"Upload return code: {upload_result.returncode}")
print(f"Upload response: {upload_result.stdout}")
if upload_result.returncode != 0:
    print(f"Upload stderr: {upload_result.stderr}")

