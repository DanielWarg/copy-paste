"""
Audio transcription using Faster-Whisper.

Transcribes audio files locally and creates transcript segments.
"""
import os
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from app.core.logging import logger

# Initialize Whisper model (load once, reuse)
_whisper_model = None


def get_whisper_model():
    """Lazy load Whisper model.
    
    Returns:
        WhisperModel instance
        
    Raises:
        ImportError: If faster-whisper is not installed
    """
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            # Use base model for speed/quality balance
            # device="cpu" for compatibility, compute_type="int8" for efficiency
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            logger.info("whisper_model_loaded", extra={"model": "base", "device": "cpu"})
        except ImportError:
            raise ImportError(
                "faster-whisper not installed. Install with: pip install faster-whisper"
            )
    return _whisper_model


def transcribe_audio(
    file_content: bytes,
    language: str = "sv",
    filename: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Transcribe audio file using Faster-Whisper.
    
    Args:
        file_content: Audio file content (bytes)
        language: Language code (default "sv" for Swedish)
        filename: Optional filename (for temp file extension)
        
    Returns:
        Tuple of (full_transcript, segments, metadata)
        
        segments: List of dicts with:
            - start_ms: Start time in milliseconds
            - end_ms: End time in milliseconds
            - text: Segment text
            - confidence: Confidence score (0.0-1.0)
        
        metadata: Dict with transcription metadata
        
    Raises:
        ValueError: If transcription fails or returns empty result
    """
    temp_path = None
    try:
        # Determine file extension
        suffix = ".wav"  # Default
        if filename:
            ext = Path(filename).suffix.lower()
            if ext in [".wav", ".mp3", ".m4a", ".aac", ".mp4", ".ogg", ".webm"]:
                suffix = ext
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(file_content)
        
        # Transcribe with Faster-Whisper
        model = get_whisper_model()
        # Try specified language first, fallback to auto-detect
        segments_iter, info = model.transcribe(
            temp_path,
            beam_size=5,
            language=language if language else None,  # None = auto-detect
            task="transcribe",
        )
        
        # CRITICAL: segments is an iterator - collect to list first
        segment_list = list(segments_iter)
        
        # Build full transcript and segments
        transcript_parts = []
        segments = []
        duration_total = 0.0
        
        for segment in segment_list:
            text = segment.text.strip()
            if not text:
                continue
                
            transcript_parts.append(text)
            
            # Convert seconds to milliseconds
            start_ms = int(segment.start * 1000)
            end_ms = int(segment.end * 1000)
            duration_total += (segment.end - segment.start)
            
            segments.append({
                "start_ms": start_ms,
                "end_ms": end_ms,
                "text": text,
                "confidence": float(segment.no_speech_prob) if hasattr(segment, 'no_speech_prob') else None,
                "speaker_label": "SPEAKER_1",  # Default, can be enhanced with diarization
            })
        
        full_transcript = " ".join(transcript_parts)
        
        # Validate transcript is not empty
        if not full_transcript or not full_transcript.strip():
            raise ValueError(
                "Transcription returned empty result. Check audio file format and quality."
            )
        
        # Build metadata
        detected_language = getattr(info, 'language', None) or language or "sv"
        words_per_minute = len(full_transcript.split()) / (duration_total / 60) if duration_total > 0 else 0
        
        metadata = {
            "language": detected_language,
            "language_probability": float(getattr(info, 'language_probability', 0.0)) if hasattr(info, 'language_probability') else None,
            "transcription_model": "faster-whisper/base",
            "duration_seconds": int(duration_total),
            "transcript_length": len(full_transcript),
            "word_count": len(full_transcript.split()),
            "words_per_minute": round(words_per_minute, 1),
            "segment_count": len(segments),
        }
        
        # Warn if transcription seems incomplete
        if duration_total > 60 and words_per_minute < 50:
            logger.warning(
                "transcription_low_wpm",
                extra={
                    "words_per_minute": words_per_minute,
                    "duration_seconds": duration_total,
                    "transcript_length": len(full_transcript),
                },
            )
        
        return full_transcript, segments, metadata
        
    except ImportError as e:
        raise ValueError(f"Transcription not available: {str(e)}")
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "transcription_failed",
            extra={"error_type": error_type, "error_message": str(e)[:200]},
        )
        raise ValueError(f"Transcription failed: {error_type}")
    finally:
        # Always delete temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass

