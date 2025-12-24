#!/usr/bin/env python3
"""Test transcripts export functions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.modules.transcripts import export

# Test export functions
segments = [
    {"start_ms": 0, "end_ms": 5000, "speaker_label": "SPEAKER_1", "text": "Test text"},
    {"start_ms": 5000, "end_ms": 10000, "speaker_label": "SPEAKER_2", "text": "More text"},
]

srt = export.export_srt(segments)
print("✅ SRT export works")
assert "00:00:00,000" in srt, "SRT format check"
assert "00:00:05,000" in srt, "SRT second segment check"

vtt = export.export_vtt(segments)
print("✅ VTT export works")
assert "WEBVTT" in vtt, "VTT format check"
assert "00:00:00.000" in vtt, "VTT time format check"

quotes = export.export_quotes(segments)
print("✅ Quotes export works")
assert len(quotes) == 2, "Quotes count check"
assert quotes[0]["speaker"] == "SPEAKER_1", "Quotes speaker check"
assert quotes[0]["start_ms"] == 0, "Quotes start_ms check"

print("\n✅ All export functions work correctly")

