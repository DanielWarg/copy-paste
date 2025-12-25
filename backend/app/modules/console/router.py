"""Console router - Events and Sources endpoints for frontend UI."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Query
from pathlib import Path

from app.core.logging import logger
from app.core.config import settings

# Privacy service (optional - may not exist)
_event_store = {}
def get_event(event_id):
    """Get event by ID (stub if privacy service not available)."""
    raise ValueError(f"Event {event_id} not found")

try:
    from app.modules.privacy.privacy_service import _event_store, get_event
except ImportError:
    # Privacy service not available - use stub
    pass

router = APIRouter()


def _has_db() -> bool:
    """Check if database is available."""
    from app.core.database import engine
    return engine is not None and settings.database_url is not None


def _load_scout_feeds() -> List[Dict[str, Any]]:
    """Load feeds from scout/feeds.yaml (if available).
    
    Returns:
        List of feed configs or empty list if not available
    """
    try:
        # Try to load from scout/feeds.yaml (relative to project root)
        feeds_path = Path(__file__).parent.parent.parent.parent.parent / "scout" / "feeds.yaml"
        if not feeds_path.exists():
            return []
        
        try:
            import yaml
        except ImportError:
            logger.warning("yaml_not_available", extra={"reason": "PyYAML not installed"})
            return []
        
        with open(feeds_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        feeds = config.get("feeds", [])
        logger.info("scout_feeds_loaded", extra={"count": len(feeds)})
        return feeds
    except Exception as e:
        error_type = type(e).__name__
        logger.warning("scout_feeds_load_failed", extra={"error_type": error_type})
        return []


def _load_scout_events() -> List[Dict[str, Any]]:
    """Load events from scout dedupe_store (if available).
    
    Returns:
        List of events or empty list if not available
    """
    try:
        # Try to import scout dedupe_store
        import sys
        scout_path = Path(__file__).parent.parent.parent.parent.parent / "scout"
        if not scout_path.exists():
            return []
        
        sys.path.insert(0, str(scout_path.parent))
        from scout.dedupe_store import dedupe_store
        
        # Get recent events (last 24 hours)
        events = dedupe_store.get_recent_events(hours=24, limit=200)
        logger.info("scout_events_loaded", extra={"count": len(events)})
        return events
    except Exception as e:
        error_type = type(e).__name__
        logger.warning("scout_events_load_failed", extra={"error_type": error_type})
        return []


def _adapt_event_to_frontend(event_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
    """Adapt backend event to frontend NewsEvent format.
    
    Args:
        event_data: Event data from in-memory store or scout
        event_id: Event ID (string)
        
    Returns:
        Frontend-compatible event dict
    """
    # Extract metadata
    metadata = event_data.get("metadata", {})
    
    # Determine source and sourceType
    source = metadata.get("scout_source", metadata.get("url", "Unknown"))
    source_type = "RSS" if "scout_source" in metadata else "MANUAL"
    
    # Determine status (simplified mapping)
    status = "INKOMMANDE"  # Default
    if metadata.get("draft_generated"):
        status = "GRANSKNING"
    elif metadata.get("scrubbed"):
        status = "PÅGÅR"
    
    # Extract score (from scout or default)
    score = metadata.get("scout_score", 50)  # Default 50 if no score
    
    # Extract timestamp
    timestamp = metadata.get("scout_detected_at") or metadata.get("created_at") or datetime.utcnow().isoformat()
    
    # Build title and summary from raw_payload (first 100 chars)
    raw_payload = event_data.get("raw_payload", "")
    title = raw_payload[:100].split("\n")[0] if raw_payload else "Untitled Event"
    summary = raw_payload[:200] if raw_payload else ""
    
    return {
        "id": event_id,
        "title": title,
        "summary": summary,
        "source": source,
        "sourceType": source_type,
        "timestamp": timestamp,
        "status": status,
        "score": score,
        "isDuplicate": False,
    }


@router.get("/events")
async def get_events(
    limit: int = Query(50, ge=1, le=200, description="Max items (default 50, max 200)"),
) -> Dict[str, Any]:
    """Get events for Console/Pipeline view.
    
    Returns:
        List of events in frontend-compatible format
    """
    logger.info("events_list", extra={"limit": limit})
    
    events = []
    
    try:
        # Try to load from in-memory store (privacy_service)
        if _event_store:
            for event_id, event in _event_store.items():
                try:
                    event_dict = {
                        "event_id": str(event.event_id),
                        "source_type": event.source_type,
                        "raw_payload": event.raw_payload[:500] if event.raw_payload else "",  # Truncate for safety
                        "metadata": event.metadata,
                    }
                    adapted = _adapt_event_to_frontend(event_dict, str(event.event_id))
                    events.append(adapted)
                except Exception as e:
                    error_type = type(e).__name__
                    logger.warning("event_adapt_failed", extra={"error_type": error_type})
                    continue
        
        # Try to load from scout dedupe_store
        scout_events = _load_scout_events()
        for scout_event in scout_events:
            try:
                event_id = scout_event.get("event_id", "")
                if event_id:
                    # Try to get full event from in-memory store
                    try:
                        from uuid import UUID
                        event = get_event(UUID(event_id))
                        event_dict = {
                            "event_id": event_id,
                            "source_type": event.source_type,
                            "raw_payload": event.raw_payload[:500] if event.raw_payload else "",
                            "metadata": {**event.metadata, **scout_event},
                        }
                    except Exception:
                        # Fallback: use scout event data only
                        event_dict = {
                            "event_id": event_id,
                            "source_type": "rss",
                            "raw_payload": "",
                            "metadata": scout_event,
                        }
                    
                    adapted = _adapt_event_to_frontend(event_dict, event_id)
                    events.append(adapted)
            except Exception as e:
                error_type = type(e).__name__
                logger.warning("scout_event_adapt_failed", extra={"error_type": error_type})
                continue
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit results
        events = events[:limit]
        
        logger.info("events_list_complete", extra={"count": len(events)})
        return {"items": events, "total": len(events), "limit": limit}
    
    except Exception as e:
        error_type = type(e).__name__
        logger.error("events_list_failed", extra={"error_type": error_type})
        # Return empty list on error (UI should still work)
        return {"items": [], "total": 0, "limit": limit}


@router.get("/events/{event_id}")
async def get_event_by_id(event_id: str) -> Dict[str, Any]:
    """Get event by ID.
    
    Args:
        event_id: Event ID (UUID string)
        
    Returns:
        Event in frontend-compatible format
    """
    logger.info("event_get", extra={"event_id": event_id})
    
    try:
        from uuid import UUID
        
        # Try to get from in-memory store
        try:
            event = get_event(UUID(event_id))
            event_dict = {
                "event_id": str(event.event_id),
                "source_type": event.source_type,
                "raw_payload": event.raw_payload,
                "metadata": event.metadata,
            }
            adapted = _adapt_event_to_frontend(event_dict, event_id)
            
            # Add optional fields if available
            if event.raw_payload:
                adapted["content"] = event.raw_payload
            
            logger.info("event_get_complete", extra={"event_id": event_id})
            return adapted
        except Exception:
            # Try scout dedupe_store
            scout_events = _load_scout_events()
            for scout_event in scout_events:
                if scout_event.get("event_id") == event_id:
                    event_dict = {
                        "event_id": event_id,
                        "source_type": "rss",
                        "raw_payload": "",
                        "metadata": scout_event,
                    }
                    adapted = _adapt_event_to_frontend(event_dict, event_id)
                    logger.info("event_get_complete", extra={"event_id": event_id})
                    return adapted
        
        # Not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        logger.error("event_get_failed", extra={"event_id": event_id, "error_type": error_type})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get event",
        )


@router.get("/sources")
async def get_sources() -> Dict[str, Any]:
    """Get sources/feeds for Sources view.
    
    Returns:
        List of sources in frontend-compatible format
    """
    logger.info("sources_list")
    
    sources = []
    
    try:
        # Load from scout/feeds.yaml
        feeds = _load_scout_feeds()
        
        for feed in feeds:
            try:
                feed_name = feed.get("name", "Unknown")
                feed_url = feed.get("url", "")
                enabled = feed.get("enabled", True)
                
                # Generate feed ID from URL
                import hashlib
                feed_id = hashlib.sha256(feed_url.encode()).hexdigest()[:12] if feed_url else "unknown"
                
                # Determine type
                feed_type = "RSS"  # Default
                if "api" in feed_url.lower() or "api" in feed_name.lower():
                    feed_type = "API"
                elif "mail" in feed_name.lower() or "email" in feed_name.lower():
                    feed_type = "MAIL"
                
                # Determine status
                status = "ACTIVE" if enabled else "PAUSED"
                
                # Try to get last fetch time from scout events
                last_fetch = "Aldrig"
                try:
                    scout_events = _load_scout_events()
                    feed_events = [e for e in scout_events if e.get("feed_url") == feed_url]
                    if feed_events:
                        # Get most recent event
                        latest = max(feed_events, key=lambda x: x.get("detected_at", ""))
                        detected_at = latest.get("detected_at", "")
                        if detected_at:
                            try:
                                dt_str = detected_at.replace("Z", "+00:00")
                                dt = datetime.fromisoformat(dt_str)
                                if dt.tzinfo:
                                    dt = dt.replace(tzinfo=None)
                                now = datetime.utcnow()
                                diff = now - dt
                                if diff.total_seconds() < 3600:
                                    last_fetch = f"{int(diff.total_seconds() / 60)} min sedan"
                                elif diff.total_seconds() < 86400:
                                    last_fetch = f"{int(diff.total_seconds() / 3600)} timmar sedan"
                                else:
                                    last_fetch = f"{int(diff.total_seconds() / 86400)} dagar sedan"
                            except Exception:
                                pass
                except Exception:
                    pass
                
                # Estimate items per day (simplified)
                items_per_day = 0
                try:
                    scout_events = _load_scout_events()
                    feed_events = [e for e in scout_events if e.get("feed_url") == feed_url]
                    # Count events from last 24 hours
                    now = datetime.utcnow()
                    recent_events = []
                    for e in feed_events:
                        detected_at = e.get("detected_at")
                        if detected_at:
                            try:
                                # Parse ISO timestamp
                                dt_str = detected_at.replace("Z", "+00:00")
                                dt = datetime.fromisoformat(dt_str)
                                if dt.tzinfo:
                                    dt = dt.replace(tzinfo=None)
                                diff = now - dt
                                if diff.total_seconds() < 86400:
                                    recent_events.append(e)
                            except Exception:
                                pass
                    items_per_day = len(recent_events)
                except Exception:
                    pass
                
                sources.append({
                    "id": f"src-{feed_id}",
                    "name": feed_name,
                    "type": feed_type,
                    "status": status,
                    "lastFetch": last_fetch,
                    "itemsPerDay": items_per_day,
                })
            except Exception as e:
                error_type = type(e).__name__
                logger.warning("source_adapt_failed", extra={"error_type": error_type})
                continue
        
        logger.info("sources_list_complete", extra={"count": len(sources)})
        return {"items": sources, "total": len(sources)}
    
    except Exception as e:
        error_type = type(e).__name__
        logger.error("sources_list_failed", extra={"error_type": error_type})
        # Return empty list on error (UI should still work)
        return {"items": [], "total": 0}

