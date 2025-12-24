"""Transcripts router - API endpoints for transcript management."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.modules.transcripts import service, export


router = APIRouter()


# Request/Response models
class TranscriptCreate(BaseModel):
    """Request model for creating a transcript."""
    title: str = Field(..., min_length=1, max_length=500)
    source: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="sv", max_length=10)
    duration_seconds: Optional[int] = Field(None, ge=0)
    status: str = Field(default="uploaded", max_length=50)


class SegmentCreate(BaseModel):
    """Request model for a transcript segment."""
    start_ms: int = Field(..., ge=0)
    end_ms: int = Field(..., ge=0)
    speaker_label: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class SegmentsUpsert(BaseModel):
    """Request model for upserting segments."""
    segments: List[SegmentCreate] = Field(..., min_items=0)


@router.get("/")
async def list_transcripts(
    q: Optional[str] = Query(None, description="Search in title, speaker_label, segment text"),
    status: Optional[str] = Query(None, description="Filter by status"),
    language: Optional[str] = Query(None, description="Filter by language"),
    source: Optional[str] = Query(None, description="Filter by source"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    limit: int = Query(50, ge=1, le=200, description="Max items (default 50, max 200)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> Dict[str, Any]:
    """List transcripts with filtering and search.
    
    Returns:
        Dict with items, total, limit, offset
    """
    logger.info(
        "transcripts_list",
        extra={
            "module": "transcripts",
            "endpoint": "/api/v1/transcripts",
            "has_query": q is not None,
            "status": status,
            "limit": limit,
            "offset": offset,
        },
    )
    
    try:
        result = service.list_transcripts(
            q=q,
            status=status,
            language=language,
            source=source,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(
            "transcripts_list_error",
            extra={
                "module": "transcripts",
                "error": str(e),
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list transcripts")


@router.get("/{transcript_id}")
async def get_transcript(
    transcript_id: int,
    include_segments: bool = Query(True, description="Include segments in response"),
) -> Dict[str, Any]:
    """Get transcript by ID.
    
    Args:
        transcript_id: Transcript ID
        include_segments: Whether to include segments
        
    Returns:
        Transcript dict with optional segments
    """
    logger.info(
        "transcript_get",
        extra={
            "module": "transcripts",
            "endpoint": f"/api/v1/transcripts/{transcript_id}",
            "transcript_id": transcript_id,
            "include_segments": include_segments,
        },
    )
    
    result = service.get_transcript(transcript_id, include_segments=include_segments)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transcript {transcript_id} not found")
    
    return result


@router.post("/")
async def create_transcript(data: TranscriptCreate) -> Dict[str, Any]:
    """Create a new transcript.
    
    Args:
        data: Transcript creation data
        
    Returns:
        Created transcript dict
    """
    logger.info(
        "transcript_create",
        extra={
            "module": "transcripts",
            "endpoint": "/api/v1/transcripts",
            "title": data.title[:50] if data.title else None,  # Only first 50 chars, no full text
            "source": data.source,
        },
    )
    
    try:
        result = service.create_transcript(
            title=data.title,
            source=data.source,
            language=data.language,
            duration_seconds=data.duration_seconds,
            status=data.status,
        )
        return result
    except Exception as e:
        logger.error(
            "transcript_create_error",
            extra={
                "module": "transcripts",
                "error": str(e),
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create transcript")


@router.post("/{transcript_id}/segments")
async def upsert_segments(transcript_id: int, data: SegmentsUpsert) -> Dict[str, Any]:
    """Upsert segments for a transcript (replace all).
    
    Args:
        transcript_id: Transcript ID
        data: Segments data
        
    Returns:
        Dict with status and segments_saved count
    """
    logger.info(
        "transcript_segments_upsert",
        extra={
            "module": "transcripts",
            "endpoint": f"/api/v1/transcripts/{transcript_id}/segments",
            "transcript_id": transcript_id,
            "segments_count": len(data.segments),
        },
    )
    
    try:
        # Convert Pydantic models to dicts
        segments_dict = [
            {
                "start_ms": seg.start_ms,
                "end_ms": seg.end_ms,
                "speaker_label": seg.speaker_label,
                "text": seg.text,
                "confidence": seg.confidence,
            }
            for seg in data.segments
        ]
        
        result = service.upsert_segments(transcript_id, segments_dict)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "transcript_segments_upsert_error",
            extra={
                "module": "transcripts",
                "transcript_id": transcript_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upsert segments")


@router.post("/{transcript_id}/export")
async def export_transcript(
    transcript_id: int,
    format: str = Query(..., description="Export format: srt, vtt, or quotes"),
) -> Dict[str, Any]:
    """Export transcript in specified format.
    
    Args:
        transcript_id: Transcript ID
        format: Export format (srt, vtt, quotes)
        
    Returns:
        Export data (format-specific)
    """
    logger.info(
        "transcript_export",
        extra={
            "module": "transcripts",
            "endpoint": f"/api/v1/transcripts/{transcript_id}/export",
            "transcript_id": transcript_id,
            "format": format,
        },
    )
    
    # Get transcript with segments
    transcript = service.get_transcript(transcript_id, include_segments=True)
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transcript {transcript_id} not found")
    
    segments = transcript.get("segments", [])
    if not segments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcript has no segments")
    
    # Convert segments to export format
    segments_for_export = [
        {
            "start_ms": s["start_ms"],
            "end_ms": s["end_ms"],
            "speaker_label": s["speaker_label"],
            "text": s["text"],
        }
        for s in segments
    ]
    
    # Export based on format
    if format == "srt":
        content = export.export_srt(segments_for_export)
        # Audit event
        _log_export_audit(transcript_id, "srt")
        return {"format": "srt", "content": content}
    elif format == "vtt":
        content = export.export_vtt(segments_for_export)
        _log_export_audit(transcript_id, "vtt")
        return {"format": "vtt", "content": content}
    elif format == "quotes":
        items = export.export_quotes(segments_for_export)
        _log_export_audit(transcript_id, "quotes")
        return {"format": "quotes", "items": items}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format: {format}. Must be srt, vtt, or quotes",
        )


def _log_export_audit(transcript_id: int, format: str) -> None:
    """Log export audit event (non-blocking)."""
    try:
        from datetime import datetime
        from app.modules.transcripts.service import _has_db
        
        if _has_db():
            from app.core.database import get_db
            from app.modules.transcripts.models import TranscriptAuditEvent
            
            with get_db() as db:
                # Audit event (sanitized for privacy)
                audit_metadata = sanitize_for_logging({"format": format}, context="audit")
                assert_no_content(audit_metadata, context="audit")
                audit = TranscriptAuditEvent(
                    transcript_id=transcript_id,
                    action="exported",
                    actor="system",
                    created_at=datetime.utcnow(),
                    metadata_json=audit_metadata,
                )
                db.add(audit)
                db.commit()
        else:
            # Memory store audit (sanitized for privacy)
            from app.modules.transcripts.service import _MEMORY_AUDIT
            audit_metadata = sanitize_for_logging({"format": format}, context="audit")
            assert_no_content(audit_metadata, context="audit")
            _MEMORY_AUDIT.append({
                "id": len(_MEMORY_AUDIT) + 1,
                "transcript_id": transcript_id,
                "action": "exported",
                "actor": "system",
                "created_at": datetime.utcnow(),
                "metadata_json": audit_metadata,
            })
    except Exception:
        # Non-blocking - don't fail export if audit fails
        pass


@router.delete("/{transcript_id}")
async def delete_transcript(transcript_id: int) -> Dict[str, Any]:
    """Delete transcript (hard delete).
    
    Args:
        transcript_id: Transcript ID
        
    Returns:
        Dict with status, receipt_id, deleted_at
    """
    logger.info(
        "transcript_delete",
        extra={
            "module": "transcripts",
            "endpoint": f"/api/v1/transcripts/{transcript_id}",
            "transcript_id": transcript_id,
        },
    )
    
    try:
        result = service.delete_transcript(transcript_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "transcript_delete_error",
            extra={
                "module": "transcripts",
                "transcript_id": transcript_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete transcript")

