"""Transcript service - handles DB and memory fallback."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from sqlalchemy import or_, func

from app.core.config import settings
from app.core.database import get_db
from app.core.privacy_guard import sanitize_for_logging, assert_no_content
from app.modules.transcripts.models import Transcript, TranscriptSegment, TranscriptAuditEvent


# Memory store for no-DB mode
_MEMORY_STORE: Dict[int, Dict[str, Any]] = {}
_MEMORY_SEGMENTS: Dict[int, List[Dict[str, Any]]] = {}
_MEMORY_AUDIT: List[Dict[str, Any]] = []
_NEXT_ID = 1


def _seed_memory_store() -> None:
    """Seed memory store with sample transcripts for dev."""
    global _NEXT_ID
    
    if _MEMORY_STORE:
        return  # Already seeded
    
    # Seed transcript 1
    t1_id = _NEXT_ID
    _MEMORY_STORE[t1_id] = {
        "id": t1_id,
        "title": "Intervju: Kommunalrådet om skolnedläggningen",
        "source": "interview",
        "language": "sv",
        "duration_seconds": 840,
        "status": "ready",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    _MEMORY_SEGMENTS[t1_id] = [
        {
            "id": 1,
            "transcript_id": t1_id,
            "start_ms": 0,
            "end_ms": 3500,
            "speaker_label": "SPEAKER_1",
            "text": "Det är ett tufft beslut, men vi måste se till ekonomin. Vi har inget val.",
            "confidence": 0.95,
            "created_at": datetime.utcnow(),
        },
        {
            "id": 2,
            "transcript_id": t1_id,
            "start_ms": 3500,
            "end_ms": 7200,
            "speaker_label": "SPEAKER_2",
            "text": "Men vad säger föräldrarna? De har rätt att vara oroliga.",
            "confidence": 0.92,
            "created_at": datetime.utcnow(),
        },
    ]
    _NEXT_ID += 1
    
    # Seed transcript 2
    t2_id = _NEXT_ID
    _MEMORY_STORE[t2_id] = {
        "id": t2_id,
        "title": "Presskonferens Polisen",
        "source": "meeting",
        "language": "sv",
        "duration_seconds": 525,
        "status": "ready",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    _MEMORY_SEGMENTS[t2_id] = [
        {
            "id": 3,
            "transcript_id": t2_id,
            "start_ms": 0,
            "end_ms": 8000,
            "speaker_label": "SPEAKER_1",
            "text": "Vi kan bekräfta att en person är frihetsberövad. Utredningen pågår.",
            "confidence": 0.98,
            "created_at": datetime.utcnow(),
        },
    ]
    _NEXT_ID += 1


def _has_db() -> bool:
    """Check if database is available."""
    # Import engine from module to get current value (not cached import)
    from app.core.database import engine
    return engine is not None and settings.database_url is not None


def list_transcripts(
    q: Optional[str] = None,
    status: Optional[str] = None,
    language: Optional[str] = None,
    source: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List transcripts with filtering and search.
    
    Args:
        q: Search query (title, speaker_label, segment text)
        status: Filter by status
        language: Filter by language
        source: Filter by source
        date_from: Filter from date (ISO format)
        date_to: Filter to date (ISO format)
        limit: Max items (default 50, max 200)
        offset: Offset for pagination
        
    Returns:
        Dict with items, total, limit, offset
    """
    limit = min(limit, 200)  # Cap at 200
    
    if _has_db():
        return _list_transcripts_db(
            q, status, language, source, date_from, date_to, limit, offset
        )
    else:
        return _list_transcripts_memory(
            q, status, language, source, date_from, date_to, limit, offset
        )


def _list_transcripts_db(
    q: Optional[str],
    status: Optional[str],
    language: Optional[str],
    source: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """List transcripts from database."""
    with get_db() as db:
        query = db.query(Transcript)
        
        # Filters
        if status:
            query = query.filter(Transcript.status == status)
        if language:
            query = query.filter(Transcript.language == language)
        if source:
            query = query.filter(Transcript.source == source)
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                query = query.filter(Transcript.created_at >= date_from_dt)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                query = query.filter(Transcript.created_at <= date_to_dt)
            except ValueError:
                pass
        
        # Search (title, speaker_label, segment text)
        if q:
            search_filter = Transcript.title.ilike(f"%{q}%")
            # Also search in segments
            segment_matches = db.query(TranscriptSegment.transcript_id).filter(
                or_(
                    TranscriptSegment.speaker_label.ilike(f"%{q}%"),
                    TranscriptSegment.text.ilike(f"%{q}%"),
                )
            ).distinct()
            search_filter = or_(search_filter, Transcript.id.in_(segment_matches))
            query = query.filter(search_filter)
        
        # Count total
        total = query.count()
        
        # Get items
        transcripts = query.order_by(Transcript.created_at.desc()).offset(offset).limit(limit).all()
        
        items = []
        for t in transcripts:
            # Get segments count
            segments_count = db.query(func.count(TranscriptSegment.id)).filter(
                TranscriptSegment.transcript_id == t.id
            ).scalar() or 0
            
            # Get preview (first 240 chars from segments)
            preview = ""
            first_segments = db.query(TranscriptSegment).filter(
                TranscriptSegment.transcript_id == t.id
            ).order_by(TranscriptSegment.start_ms).limit(3).all()
            if first_segments:
                preview_text = " ".join(s.text for s in first_segments)
                preview = preview_text[:240] + ("..." if len(preview_text) > 240 else "")
            
            items.append({
                "id": t.id,
                "title": t.title,
                "source": t.source,
                "language": t.language,
                "duration_seconds": t.duration_seconds,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
                "segments_count": segments_count,
                "preview": preview,
            })
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


def _list_transcripts_memory(
    q: Optional[str],
    status: Optional[str],
    language: Optional[str],
    source: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """List transcripts from memory store."""
    _seed_memory_store()
    
    items = []
    for t_id, t in _MEMORY_STORE.items():
        # Filters
        if status and t["status"] != status:
            continue
        if language and t["language"] != language:
            continue
        if source and t["source"] != source:
            continue
        
        # Search
        if q:
            q_lower = q.lower()
            if q_lower not in t["title"].lower():
                # Check segments
                found = False
                for seg in _MEMORY_SEGMENTS.get(t_id, []):
                    if q_lower in seg.get("speaker_label", "").lower() or q_lower in seg.get("text", "").lower():
                        found = True
                        break
                if not found:
                    continue
        
        items.append(t)
    
    # Sort by created_at desc
    items.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Add segments_count and preview
    result_items = []
    for t in items[offset:offset + limit]:
        segments = _MEMORY_SEGMENTS.get(t["id"], [])
        preview = ""
        if segments:
            preview_text = " ".join(s.get("text", "") for s in segments[:3])
            preview = preview_text[:240] + ("..." if len(preview_text) > 240 else "")
        
        result_items.append({
            "id": t["id"],
            "title": t["title"],
            "source": t["source"],
            "language": t["language"],
            "duration_seconds": t["duration_seconds"],
            "status": t["status"],
            "created_at": t["created_at"].isoformat(),
            "updated_at": t["updated_at"].isoformat(),
            "segments_count": len(segments),
            "preview": preview,
        })
    
    return {
        "items": result_items,
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }


def get_transcript(transcript_id: int, include_segments: bool = True) -> Optional[Dict[str, Any]]:
    """Get transcript by ID.
    
    Args:
        transcript_id: Transcript ID
        include_segments: Whether to include segments
        
    Returns:
        Transcript dict or None if not found
    """
    if _has_db():
        return _get_transcript_db(transcript_id, include_segments)
    else:
        return _get_transcript_memory(transcript_id, include_segments)


def _get_transcript_db(transcript_id: int, include_segments: bool) -> Optional[Dict[str, Any]]:
    """Get transcript from database."""
    with get_db() as db:
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            return None
        
        result = {
            "id": transcript.id,
            "title": transcript.title,
            "source": transcript.source,
            "language": transcript.language,
            "duration_seconds": transcript.duration_seconds,
            "status": transcript.status,
            "created_at": transcript.created_at.isoformat(),
            "updated_at": transcript.updated_at.isoformat(),
        }
        
        if include_segments:
            segments = db.query(TranscriptSegment).filter(
                TranscriptSegment.transcript_id == transcript_id
            ).order_by(TranscriptSegment.start_ms).all()
            result["segments"] = [
                {
                    "id": s.id,
                    "start_ms": s.start_ms,
                    "end_ms": s.end_ms,
                    "speaker_label": s.speaker_label,
                    "text": s.text,
                    "confidence": s.confidence,
                    "created_at": s.created_at.isoformat(),
                }
                for s in segments
            ]
        
        return result


def _get_transcript_memory(transcript_id: int, include_segments: bool) -> Optional[Dict[str, Any]]:
    """Get transcript from memory store."""
    _seed_memory_store()
    
    transcript = _MEMORY_STORE.get(transcript_id)
    if not transcript:
        return None
    
    result = {
        "id": transcript["id"],
        "title": transcript["title"],
        "source": transcript["source"],
        "language": transcript["language"],
        "duration_seconds": transcript["duration_seconds"],
        "status": transcript["status"],
        "created_at": transcript["created_at"].isoformat(),
        "updated_at": transcript["updated_at"].isoformat(),
    }
    
    if include_segments:
        segments = _MEMORY_SEGMENTS.get(transcript_id, [])
        result["segments"] = [
            {
                "id": s["id"],
                "start_ms": s["start_ms"],
                "end_ms": s["end_ms"],
                "speaker_label": s["speaker_label"],
                "text": s["text"],
                "confidence": s.get("confidence"),
                "created_at": s["created_at"].isoformat(),
            }
            for s in segments
        ]
    
    return result


def create_transcript(
    title: str,
    source: str,
    language: str = "sv",
    duration_seconds: Optional[int] = None,
    status: str = "uploaded",
) -> Dict[str, Any]:
    """Create a new transcript.
    
    Args:
        title: Transcript title
        source: Source type (interview, meeting, upload)
        language: Language code (default "sv")
        duration_seconds: Duration in seconds
        status: Initial status
        
    Returns:
        Created transcript dict
    """
    if _has_db():
        return _create_transcript_db(title, source, language, duration_seconds, status)
    else:
        return _create_transcript_memory(title, source, language, duration_seconds, status)


def _create_transcript_db(
    title: str,
    source: str,
    language: str,
    duration_seconds: Optional[int],
    status: str,
) -> Dict[str, Any]:
    """Create transcript in database."""
    with get_db() as db:
        transcript = Transcript(
            title=title,
            source=source,
            language=language,
            duration_seconds=duration_seconds,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        # Audit event (sanitized for privacy)
        audit_metadata = sanitize_for_logging({"title": title, "source": source}, context="audit")
        assert_no_content(audit_metadata, context="audit")
        audit = TranscriptAuditEvent(
            transcript_id=transcript.id,
            action="created",
            actor="system",
            created_at=datetime.utcnow(),
            metadata_json=audit_metadata,
        )
        db.add(audit)
        db.commit()
        
        return {
            "id": transcript.id,
            "title": transcript.title,
            "source": transcript.source,
            "language": transcript.language,
            "duration_seconds": transcript.duration_seconds,
            "status": transcript.status,
            "created_at": transcript.created_at.isoformat(),
            "updated_at": transcript.updated_at.isoformat(),
        }


def _create_transcript_memory(
    title: str,
    source: str,
    language: str,
    duration_seconds: Optional[int],
    status: str,
) -> Dict[str, Any]:
    """Create transcript in memory store."""
    global _NEXT_ID
    _seed_memory_store()
    
    transcript_id = _NEXT_ID
    _NEXT_ID += 1
    
    now = datetime.utcnow()
    transcript = {
        "id": transcript_id,
        "title": title,
        "source": source,
        "language": language,
        "duration_seconds": duration_seconds,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    _MEMORY_STORE[transcript_id] = transcript
    _MEMORY_SEGMENTS[transcript_id] = []
    
    # Audit event (sanitized for privacy)
    audit_metadata = sanitize_for_logging({"title": title, "source": source}, context="audit")
    assert_no_content(audit_metadata, context="audit")
    _MEMORY_AUDIT.append({
        "id": len(_MEMORY_AUDIT) + 1,
        "transcript_id": transcript_id,
        "action": "created",
        "actor": "system",
        "created_at": now,
        "metadata_json": audit_metadata,
    })
    
    return {
        "id": transcript["id"],
        "title": transcript["title"],
        "source": transcript["source"],
        "language": transcript["language"],
        "duration_seconds": transcript["duration_seconds"],
        "status": transcript["status"],
        "created_at": transcript["created_at"].isoformat(),
        "updated_at": transcript["updated_at"].isoformat(),
    }


def upsert_segments(transcript_id: int, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Upsert segments for a transcript (replace all).
    
    Args:
        transcript_id: Transcript ID
        segments: List of segment dicts with start_ms, end_ms, speaker_label, text, confidence
        
    Returns:
        Dict with status and segments_saved count
    """
    # Validate segments
    for seg in segments:
        if seg["start_ms"] >= seg["end_ms"]:
            raise ValueError(f"Invalid segment: start_ms ({seg['start_ms']}) must be < end_ms ({seg['end_ms']})")
    
    # Sort by start_ms
    segments = sorted(segments, key=lambda x: x["start_ms"])
    
    if _has_db():
        return _upsert_segments_db(transcript_id, segments)
    else:
        return _upsert_segments_memory(transcript_id, segments)


def _upsert_segments_db(transcript_id: int, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Upsert segments in database."""
    with get_db() as db:
        # Verify transcript exists
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Delete existing segments
        db.query(TranscriptSegment).filter(TranscriptSegment.transcript_id == transcript_id).delete()
        
        # Insert new segments
        for seg in segments:
            segment = TranscriptSegment(
                transcript_id=transcript_id,
                start_ms=seg["start_ms"],
                end_ms=seg["end_ms"],
                speaker_label=seg["speaker_label"],
                text=seg["text"],
                confidence=seg.get("confidence"),
                created_at=datetime.utcnow(),
            )
            db.add(segment)
        
        # Update transcript
        transcript.updated_at = datetime.utcnow()
        transcript.status = "ready"  # Auto-set to ready when segments added
        
        # Audit event (sanitized for privacy)
        audit_metadata = sanitize_for_logging({"segments_saved": len(segments)}, context="audit")
        assert_no_content(audit_metadata, context="audit")
        audit = TranscriptAuditEvent(
            transcript_id=transcript_id,
            action="segments_upserted",
            actor="system",
            created_at=datetime.utcnow(),
            metadata_json=audit_metadata,
        )
        db.add(audit)
        
        db.commit()
        
        return {"status": "ok", "segments_saved": len(segments)}


def _upsert_segments_memory(transcript_id: int, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Upsert segments in memory store."""
    _seed_memory_store()
    
    if transcript_id not in _MEMORY_STORE:
        raise ValueError(f"Transcript {transcript_id} not found")
    
    # Replace all segments
    _MEMORY_SEGMENTS[transcript_id] = []
    for idx, seg in enumerate(segments, start=1):
        _MEMORY_SEGMENTS[transcript_id].append({
            "id": idx,
            "transcript_id": transcript_id,
            "start_ms": seg["start_ms"],
            "end_ms": seg["end_ms"],
            "speaker_label": seg["speaker_label"],
            "text": seg["text"],
            "confidence": seg.get("confidence"),
            "created_at": datetime.utcnow(),
        })
    
    # Update transcript
    _MEMORY_STORE[transcript_id]["updated_at"] = datetime.utcnow()
    _MEMORY_STORE[transcript_id]["status"] = "ready"
    
    # Audit event (sanitized for privacy)
    audit_metadata = sanitize_for_logging({"segments_saved": len(segments)}, context="audit")
    assert_no_content(audit_metadata, context="audit")
    _MEMORY_AUDIT.append({
        "id": len(_MEMORY_AUDIT) + 1,
        "transcript_id": transcript_id,
        "action": "segments_upserted",
        "actor": "system",
        "created_at": datetime.utcnow(),
        "metadata_json": audit_metadata,
    })
    
    return {"status": "ok", "segments_saved": len(segments)}


def delete_transcript(transcript_id: int) -> Dict[str, Any]:
    """Delete transcript (hard delete).
    
    Args:
        transcript_id: Transcript ID
        
    Returns:
        Dict with status, receipt_id, deleted_at
    """
    receipt_id = str(uuid4())
    deleted_at = datetime.utcnow()
    
    if _has_db():
        _delete_transcript_db(transcript_id, receipt_id, deleted_at)
    else:
        _delete_transcript_memory(transcript_id, receipt_id, deleted_at)
    
    return {
        "status": "deleted",
        "receipt_id": receipt_id,
        "deleted_at": deleted_at.isoformat(),
    }


def _delete_transcript_db(transcript_id: int, receipt_id: str, deleted_at: datetime) -> None:
    """Delete transcript from database."""
    with get_db() as db:
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Audit event (before delete)
        audit = TranscriptAuditEvent(
            transcript_id=transcript_id,
            action="deleted",
            actor="system",
            created_at=deleted_at,
            metadata_json={"receipt_id": receipt_id, "mode": "hard"},
        )
        db.add(audit)
        
        # Hard delete (CASCADE will delete segments and audit events)
        db.delete(transcript)
        db.commit()


def _delete_transcript_memory(transcript_id: int, receipt_id: str, deleted_at: datetime) -> None:
    """Delete transcript from memory store."""
    _seed_memory_store()
    
    if transcript_id not in _MEMORY_STORE:
        raise ValueError(f"Transcript {transcript_id} not found")
    
    # Audit event (sanitized for privacy)
    audit_metadata = sanitize_for_logging({"receipt_id": receipt_id, "mode": "hard"}, context="audit")
    assert_no_content(audit_metadata, context="audit")
    _MEMORY_AUDIT.append({
        "id": len(_MEMORY_AUDIT) + 1,
        "transcript_id": transcript_id,
        "action": "deleted",
        "actor": "system",
        "created_at": deleted_at,
        "metadata_json": audit_metadata,
    })
    
    # Hard delete
    del _MEMORY_STORE[transcript_id]
    if transcript_id in _MEMORY_SEGMENTS:
        del _MEMORY_SEGMENTS[transcript_id]

