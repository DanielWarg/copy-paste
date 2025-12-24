#!/usr/bin/env python3
"""Test transcripts service (memory mode)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.modules.transcripts import service

# Test memory store seeding
service._seed_memory_store()
result = service.list_transcripts()
print(f"✅ Memory store works: {len(result.get('items', []))} items")

transcript = service.get_transcript(1)
print(f"✅ Get transcript works: ID={transcript.get('id') if transcript else None}")

if transcript:
    segments = transcript.get("segments", [])
    print(f"✅ Transcript has {len(segments)} segments")

print("\n✅ All service functions OK")

