"""
Audio ingestion - Local transcription using Faster-Whisper.

Transcribes audio locally, then feeds transcript into existing ingestion pipeline.
"""
import os
import tempfile
from uuid import UUID
from fastapi import UploadFile, HTTPException
from app.modules.ingestion.event_creator import create_event
from app.modules.privacy.privacy_service import store_event
from app.core.logging import log_privacy_safe

# Initialize Whisper model (load once, reuse)
_whisper_model = None


def get_whisper_model():
    """Lazy load Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="faster-whisper not installed. Install with: pip install faster-whisper"
            )
    return _whisper_model


async def ingest_audio(
    audio_file: UploadFile,
    metadata: dict = None
) -> UUID:
    """
    Ingest audio file: transcribe locally, then create event.
    
    Args:
        audio_file: Uploaded audio file
        metadata: Optional metadata
        
    Returns:
        event_id
        
    Raises:
        HTTPException: If transcription fails
    """
    temp_path = None
    try:
        # Save to temp file
        suffix = os.path.splitext(audio_file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            content = await audio_file.read()
            tmp.write(content)
        
        # Transcribe with Swedish language detection/hint
        model = get_whisper_model()
        # Try Swedish first, fallback to auto-detect
        segments, info = model.transcribe(temp_path, beam_size=5, language="sv", task="transcribe")
        
        # CRITICAL: segments is an iterator - collect to list first
        segment_list = list(segments)
        
        transcript_parts = []
        duration_total = 0.0
        for segment in segment_list:
            transcript_parts.append(segment.text)
            duration_total += (segment.end - segment.start)
        
        transcript = " ".join(transcript_parts)
        
        # Validate transcript is not empty
        if not transcript or not transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="Transcription returned empty result. Check audio file format and quality."
            )
        
        # Validate transcript completeness (warn if very short compared to duration)
        # Rough estimate: Swedish speech is ~150 words/minute, so 7.5 minutes should be ~1125 words
        # If transcript is much shorter, it might be incomplete
        words_per_minute_estimate = len(transcript.split()) / (duration_total / 60) if duration_total > 0 else 0
        if duration_total > 60 and words_per_minute_estimate < 50:  # Very low WPM suggests issues
            log_privacy_safe(
                "audio_ingest",
                f"Warning: Low transcription rate detected",
                words_per_minute=words_per_minute_estimate,
                duration=duration_total,
                transcript_length=len(transcript)
            )
        
        # Add transcription metadata
        detected_language = getattr(info, 'language', None) or "sv"
        transcript_meta = {
            "source_type": "audio",
            "filename": audio_file.filename,
            "language": detected_language,
            "language_probability": getattr(info, 'language_probability', None),
            "transcription_model": "faster-whisper/base",
            "duration_estimate": duration_total,
            "transcript_length": len(transcript),
            "word_count": len(transcript.split()),
            "words_per_minute": round(words_per_minute_estimate, 1),
            "segment_count": len(segment_list)
        }
        
        if metadata:
            transcript_meta.update(metadata)
        
        # Create event using existing ingestion (treat transcript as text)
        event = await create_event(
            input_type="text",
            value=transcript,
            metadata=transcript_meta
        )
        
        # Store event
        store_event(event)
        
        log_privacy_safe(
            str(event.event_id),
            "Audio ingested and transcribed",
            filename=audio_file.filename,
            transcript_length=len(transcript)
        )
        
        return event.event_id
        
    except Exception as e:
        log_privacy_safe("audio_ingest", f"Error ingesting audio: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error ingesting audio: {str(e)}")
    finally:
        # Always delete temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass

