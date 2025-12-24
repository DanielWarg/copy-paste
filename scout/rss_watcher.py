"""
RSS Watcher - Polls RSS feeds and creates events via /api/v1/ingest.

Producer-only: Never fetches article content, only posts URL or fallback text.
"""
import feedparser
import httpx
import hashlib
import yaml
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
try:
    from scout.dedupe_store import dedupe_store
    from scout.scorer import scorer
    from scout.config_store import config_store
    from scout.notifier import notifier
except ImportError:
    # For relative imports when running as module
    from dedupe_store import dedupe_store
    from scorer import scorer
    from config_store import config_store
    from notifier import notifier

logger = logging.getLogger(__name__)


class RSSWatcher:
    """
    Watches RSS feeds and creates events via backend API.
    """
    
    def __init__(self, backend_url: str, feeds_config_path: str = "feeds.yaml"):
        """
        Initialize RSS watcher.
        
        Args:
            backend_url: Backend API URL (e.g., http://backend:8000)
            feeds_config_path: Path to feeds.yaml configuration (baseline)
        """
        self.backend_url = backend_url.rstrip("/")
        self.feeds_config_path = feeds_config_path
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration (baseline + runtime merged)."""
        return config_store.get_effective_config()
    
    def _generate_feed_id(self, feed_url: str) -> str:
        """Generate deterministic feed ID from URL."""
        return hashlib.sha256(feed_url.encode()).hexdigest()[:12]
    
    def _compute_dedupe_key(self, item: Dict[str, Any], feed_url: str) -> str:
        """
        Compute dedupe-key in order: guid → link → hash(title+published+feed).
        
        Args:
            item: RSS item dict
            feed_url: Feed URL
            
        Returns:
            Dedupe key string
        """
        # Priority 1: guid/id
        if item.get("id"):
            return f"guid:{item['id']}"
        
        # Priority 2: link
        link = item.get("link", "").strip()
        if link:
            return f"link:{link}"
        
        # Priority 3: hash(title+published+feed)
        title = item.get("title", "")
        published = item.get("published", "")
        combined = f"{title}|{published}|{feed_url}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return f"hash:{hash_value}"
    
    async def _post_to_ingest(
        self,
        input_type: str,
        value: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Post item to /api/v1/ingest endpoint.
        
        Args:
            input_type: "url" or "text"
            value: URL or text content
            metadata: Metadata dict (will be passed to backend)
            
        Returns:
            Event ID if successful, None otherwise
        """
        try:
            # Note: Backend IngestRequest doesn't have metadata field yet
            # We'll need to add it, but for now we'll pass it and backend can ignore it
            # or we can extend the endpoint to accept optional metadata
            response = await self.client.post(
                f"{self.backend_url}/api/v1/mcp/ingest",
                json={
                    "tool": "ingest",
                    "input_type": input_type,
                    "value": value,
                    "metadata": metadata
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Handle MCP-style response (ok/error) or legacy response (event_id directly)
            if "ok" in result:
                if not result.get("ok"):
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"MCP ingest failed: {error_msg}")
                    return None
                event_id = result.get("event_id")
            else:
                # Legacy response format (backward compatibility)
                event_id = result.get("event_id")
            
            if event_id:
                logger.info(f"Created event {event_id} via MCP ingest API")
            return event_id
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error posting to ingest: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error posting to ingest: {e}")
            return None
    
    async def poll_feed(self, feed_config: Dict[str, Any]) -> int:
        """
        Poll a single RSS feed and process new items.
        
        Args:
            feed_config: Feed configuration dict (must have id, url, name)
            
        Returns:
            Number of new items processed
        """
        if not feed_config.get("enabled", True):
            logger.debug(f"Skipping disabled feed: {feed_config.get('name')}")
            return 0
        
        feed_url = feed_config["url"]
        feed_id = feed_config.get("id") or self._generate_feed_id(feed_url)
        feed_name = feed_config.get("name", feed_url)
        
        try:
            # Fetch RSS feed (follow redirects)
            response = await self.client.get(feed_url, timeout=10.0, follow_redirects=True)
            response.raise_for_status()
            
            # Parse RSS
            feed = feedparser.parse(response.text)
            
            if feed.bozo:
                logger.warning(f"Feed parse warning for {feed_name}: {feed.bozo_exception}")
            
            new_items_count = 0
            detected_at = datetime.utcnow().isoformat()
            
            # Process each item
            for item in feed.entries:
                # Compute dedupe key
                dedupe_key = self._compute_dedupe_key(item, feed_url)
                
                # Check if already seen (within last 10 hours)
                # Items older than 10 hours can be polled again
                if dedupe_store.is_seen(dedupe_key, max_age_hours=10):
                    continue
                
                # Optional scoring
                score = scorer.score(item, feed_name)
                score_threshold = feed_config.get("score_threshold")
                
                # Skip if below threshold
                if score_threshold and score < score_threshold:
                    logger.debug(f"Item score {score} below threshold {score_threshold}, skipping")
                    continue
                
                # Prepare metadata
                metadata = {
                    "scout_source": feed_name,
                    "scout_feed_id": feed_id,
                    "scout_feed_url": feed_url,
                    "scout_dedupe_key": dedupe_key,
                    "scout_score": score,
                    "scout_detected_at": detected_at,
                }
                
                # Determine input type and value
                link = item.get("link", "").strip()
                
                if link:
                    # Post URL
                    input_type = "url"
                    value = link
                    metadata["scout_item_url"] = link
                else:
                    # Fallback: post text (title + description)
                    input_type = "text"
                    title = item.get("title", "")
                    description = item.get("description", "")
                    value = f"{title}\n\n{description}".strip()
                    metadata["partial_content"] = True
                
                # Post to ingest
                event_id = await self._post_to_ingest(input_type, value, metadata)
                
                if event_id:
                    # Mark as seen with feed_id and score
                    from uuid import UUID
                    dedupe_store.mark_seen(
                        dedupe_key=dedupe_key,
                        feed_id=feed_id,
                        feed_url=feed_url,
                        event_id=UUID(event_id) if isinstance(event_id, str) else event_id,
                        detected_at=detected_at,
                        score=score
                    )
                    new_items_count += 1
                    logger.info(f"Processed new item from {feed_name}: {dedupe_key[:20]}...")
                    
                    # Auto-notify if conditions met
                    feed_notifications = feed_config.get("notifications", {})
                    default_notifications = self._get_effective_config().get("default_notifications", {})
                    
                    notifications_enabled = feed_notifications.get("enabled", default_notifications.get("enabled", False))
                    min_score = feed_notifications.get("min_score", default_notifications.get("min_score", 8))
                    
                    if notifications_enabled and score >= min_score:
                        # Send notification
                        success = notifier.send_teams(
                            event_id=str(event_id),
                            feed_id=feed_id,
                            feed_name=feed_name,
                            score=score,
                            link=link if link else None
                        )
                        if success:
                            dedupe_store.mark_notified(str(event_id))
                            logger.info(f"Auto-notified for event {event_id} (score {score})")
            
            logger.info(f"Polled {feed_name}: {new_items_count} new items")
            return new_items_count
            
        except httpx.RequestError as e:
            logger.error(f"Request error polling {feed_name}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error polling {feed_name}: {e}")
            return 0
    
    async def poll_all_feeds(self) -> Dict[str, int]:
        """
        Poll all enabled feeds.
        
        Returns:
            Dict mapping feed names to number of new items
        """
        results = {}
        effective_config = self._get_effective_config()
        
        for feed_config in effective_config.get("feeds", []):
            if feed_config.get("enabled", True):
                feed_name = feed_config.get("name", feed_config.get("url", "unknown"))
                count = await self.poll_feed(feed_config)
                results[feed_name] = count
        
        return results


# Global instance (will be initialized by scheduler)
rss_watcher: Optional[RSSWatcher] = None

