"""
Scout API - HTTP endpoints for events, feed admin, and notifications.

Minimal UI endpoints for Console.
"""
from fastapi import FastAPI, Query, HTTPException, Header, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from typing import Optional, Dict, Any
import os
import logging
import json
from datetime import datetime

try:
    from scout.dedupe_store import dedupe_store
    from scout.config_store import config_store
    from scout.notifier import notifier
except ImportError:
    # For relative imports when running as module
    from dedupe_store import dedupe_store
    from config_store import config_store
    from notifier import notifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# #region agent log
log_path = "/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE/.cursor/debug.log"
def _log_debug(location: str, message: str, data: dict, hypothesis_id: str = None):
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            log_entry = {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "location": location,
                "message": message,
                "data": data,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
# #endregion

app = FastAPI(title="Scout RSS Watcher API")

# #region agent log
_log_debug("scout/api.py:26", "FastAPI app created", {"app_id": id(app)}, "A")
# #endregion

# CORS middleware - allow frontend to access Scout API (must be added FIRST so it runs FIRST)
# #region agent log
_log_debug("scout/api.py:29", "Before CORS middleware registration", {"allow_origins": ["http://localhost:3000"], "middleware_count_before": len(app.user_middleware)}, "A")
# #endregion
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# #region agent log
_log_debug("scout/api.py:35", "After CORS middleware registration", {"middleware_count_after": len(app.user_middleware), "middleware_types": [str(type(m.cls)) for m in app.user_middleware]}, "A")
# #endregion

security = HTTPBearer(auto_error=False)


def check_admin_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """Check admin token if SCOUT_ADMIN_TOKEN is set."""
    admin_token = os.getenv("SCOUT_ADMIN_TOKEN")
    if not admin_token:
        return True  # No token required if env var not set
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    if credentials.credentials != admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    return True


def check_write_allowed() -> bool:
    """Check if config write is allowed."""
    if not os.getenv("SCOUT_ALLOW_CONFIG_WRITE", "false").lower() == "true":
        raise HTTPException(status_code=403, detail="Config write not allowed (SCOUT_ALLOW_CONFIG_WRITE=false)")
    return True


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/scout/test-cors")
async def test_cors(request: Request):
    """Test endpoint to verify CORS is working."""
    # #region agent log
    origin = request.headers.get("origin", "none")
    _log_debug("scout/api.py:test_cors", "test_cors endpoint called", {"origin": origin, "method": request.method}, "C")
    # #endregion
    return {"status": "ok", "cors_test": True, "origin": origin}


@app.get("/scout/events")
async def get_events(
    request: Request,
    hours: int = Query(default=24, ge=1, le=168),
    min_score: Optional[int] = Query(default=None, ge=1, le=10),
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    Get recent events from Scout.
    
    Args:
        hours: Number of hours to look back (1-168)
        min_score: Optional minimum score filter (1-10)
        limit: Maximum number of events (1-200)
        
    Returns:
        List of events with event_id, feed_id, feed_url, detected_at, score, notification_sent
    """
    # #region agent log
    origin = request.headers.get("origin", "none")
    _log_debug("scout/api.py:68", "get_events endpoint called", {"origin": origin, "method": request.method}, "D")
    # #endregion
    try:
        events = dedupe_store.get_recent_events(hours=hours, min_score=min_score, limit=limit)
        return {
            "events": events,
            "count": len(events),
            "hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return {"events": [], "count": 0, "error": str(e)}


@app.get("/scout/feeds")
async def get_feeds():
    """
    Get effective feed configuration (merged baseline + runtime).
    
    Returns:
        Effective config with resolved defaults
    """
    try:
        config = config_store.get_effective_config()
        return {
            "default_poll_interval": config["default_poll_interval"],
            "default_notifications": config["default_notifications"],
            "feeds": config["feeds"]
        }
    except Exception as e:
        logger.error(f"Error getting feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scout/feeds")
async def add_feed(
    feed: Dict[str, Any],
    _: bool = Depends(check_admin_token),
    __: bool = Depends(check_write_allowed)
):
    """
    Add a new feed.
    
    Body:
        {
            "name": "Feed Name",
            "url": "https://example.com/rss",
            "poll_interval": 900,  # optional
            "score_threshold": 6,  # optional
            "notifications": {  # optional
                "enabled": true,
                "min_score": 8
            }
        }
    
    Returns:
        Created feed with ID
    """
    try:
        created_feed = config_store.add_feed(feed)
        return created_feed
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/scout/feeds/{feed_id}")
async def update_feed(
    feed_id: str,
    updates: Dict[str, Any],
    _: bool = Depends(check_admin_token),
    __: bool = Depends(check_write_allowed)
):
    """
    Update feed configuration.
    
    Body:
        {
            "enabled": true,  # optional
            "poll_interval": 900,  # optional
            "score_threshold": 6,  # optional
            "notifications": {...},  # optional
            "name": "New Name"  # optional
        }
    
    Returns:
        Updated feed
    """
    try:
        updated_feed = config_store.update_feed(feed_id, updates)
        return updated_feed
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/scout/feeds/{feed_id}")
async def delete_feed(
    feed_id: str,
    _: bool = Depends(check_admin_token),
    __: bool = Depends(check_write_allowed)
):
    """
    Delete feed (mark as deleted in runtime config).
    
    Returns:
        {"ok": true}
    """
    try:
        config_store.delete_feed(feed_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scout/feeds/{feed_id}/poll")
async def poll_feed_now(feed_id: str):
    """
    Trigger immediate poll of a feed (for demo/testing).
    
    Returns:
        {"ok": true, "new_items": int}
    """
    try:
        # Import here to avoid circular dependency
        # Add scout directory to path if needed
        import sys
        import os as os_module
        scout_dir = os_module.path.dirname(os_module.path.abspath(__file__))
        if scout_dir not in sys.path:
            sys.path.insert(0, scout_dir)
        
        # Try imports in order (relative first, then absolute)
        try:
            from rss_watcher import RSSWatcher
        except ImportError:
            try:
                from scout.rss_watcher import RSSWatcher
            except ImportError:
                raise ImportError("Could not import RSSWatcher")
        
        config = config_store.get_effective_config()
        feed = None
        
        for f in config.get("feeds", []):
            if f.get("id") == feed_id:
                feed = f
                break
        
        if not feed:
            raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")
        
        # Get backend URL from env
        backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
        # Use feeds_config_path from env or default
        feeds_config_path = os.getenv("FEEDS_CONFIG", "feeds.yaml")
        watcher = RSSWatcher(backend_url, feeds_config_path)
        
        # Poll feed
        new_items = await watcher.poll_feed(feed)
        
        return {"ok": True, "new_items": new_items}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error polling feed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scout/config/status")
async def get_config_status():
    """
    Get configuration status.
    
    Returns:
        {
            "teams_configured": bool,
            "notifications_enabled": bool,
            "default_min_score": int,
            "feed_count": int
        }
    """
    try:
        config = config_store.get_effective_config()
        teams_configured = bool(os.getenv("TEAMS_WEBHOOK_URL"))
        
        default_notifications = config.get("default_notifications", {})
        notifications_enabled = default_notifications.get("enabled", False)
        default_min_score = default_notifications.get("min_score", 8)
        
        feed_count = len(config.get("feeds", []))
        
        return {
            "teams_configured": teams_configured,
            "notifications_enabled": notifications_enabled,
            "default_min_score": default_min_score,
            "feed_count": feed_count
        }
    except Exception as e:
        logger.error(f"Error getting config status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scout/notify")
async def send_notification(request: Dict[str, Any]):
    """
    Send Teams notification for an event (manual trigger).
    
    Body:
        {"event_id": "uuid"}
    
    Returns:
        {"ok": true/false, "error": "..."}
    """
    try:
        event_id = request.get("event_id")
        if not event_id:
            raise HTTPException(status_code=400, detail="event_id required")
        
        # Get event from dedupe store
        event = dedupe_store.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        
        # Get feed name from config
        config = config_store.get_effective_config()
        feed_name = event.get("feed_url", "Unknown")
        
        for feed in config.get("feeds", []):
            if feed.get("id") == event.get("feed_id"):
                feed_name = feed.get("name", feed_name)
                break
        
        # Send notification
        success = notifier.send_teams(
            event_id=event_id,
            feed_id=event.get("feed_id", ""),
            feed_name=feed_name,
            score=event.get("score", 5),
            link=None  # Link not stored in dedupe store
        )
        
        if success:
            dedupe_store.mark_notified(event_id)
            return {"ok": True}
        else:
            return {"ok": False, "error": "Failed to send notification"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return {"ok": False, "error": str(e)}
