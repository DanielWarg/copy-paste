"""Export utilities for transcripts (SRT, VTT, Quotes)."""
from typing import List, Dict, Any


def format_time_srt(ms: int) -> str:
    """Format milliseconds to SRT time format (HH:MM:SS,mmm)."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def format_time_vtt(ms: int) -> str:
    """Format milliseconds to VTT time format (HH:MM:SS.mmm)."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def export_srt(segments: List[Dict[str, Any]]) -> str:
    """Export segments as SRT format.
    
    Args:
        segments: List of segment dicts with start_ms, end_ms, text
        
    Returns:
        SRT formatted string
    """
    lines = []
    for idx, segment in enumerate(segments, start=1):
        start_ms = segment["start_ms"]
        end_ms = segment["end_ms"]
        text = segment["text"].strip()
        
        lines.append(str(idx))
        lines.append(f"{format_time_srt(start_ms)} --> {format_time_srt(end_ms)}")
        lines.append(text)
        lines.append("")  # Empty line between cues
    
    return "\n".join(lines)


def export_vtt(segments: List[Dict[str, Any]]) -> str:
    """Export segments as WebVTT format.
    
    Args:
        segments: List of segment dicts with start_ms, end_ms, text, speaker_label
        
    Returns:
        VTT formatted string
    """
    lines = ["WEBVTT", ""]
    
    for segment in segments:
        start_ms = segment["start_ms"]
        end_ms = segment["end_ms"]
        text = segment["text"].strip()
        speaker_label = segment.get("speaker_label", "")
        
        # VTT cue with optional speaker
        cue_text = f"<v {speaker_label}>{text}" if speaker_label else text
        
        lines.append(f"{format_time_vtt(start_ms)} --> {format_time_vtt(end_ms)}")
        lines.append(cue_text)
        lines.append("")  # Empty line between cues
    
    return "\n".join(lines)


def export_quotes(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Export segments as quotes format (simple list with speaker + timestamps).
    
    Args:
        segments: List of segment dicts with start_ms, end_ms, text, speaker_label
        
    Returns:
        List of quote dicts
    """
    quotes = []
    for segment in segments:
        quotes.append({
            "speaker": segment.get("speaker_label", ""),
            "start_ms": segment["start_ms"],
            "end_ms": segment["end_ms"],
            "text": segment["text"].strip(),
        })
    return quotes

