"""
Config Store - Manages baseline (feeds.yaml) + runtime overrides.

GDPR: No raw content stored. Only feed metadata.
"""
import os
import yaml
import hashlib
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigStore:
    """
    Manages feed configuration: baseline (feeds.yaml) + runtime overrides.
    
    Runtime overrides are stored in scout/data/feeds.runtime.yaml
    and only written if SCOUT_ALLOW_CONFIG_WRITE=true.
    """
    
    def __init__(self, baseline_path: str = "feeds.yaml", runtime_path: str = "data/feeds.runtime.yaml"):
        """
        Initialize config store.
        
        Args:
            baseline_path: Path to baseline feeds.yaml (read-only)
            runtime_path: Path to runtime overrides (write if allowed)
        """
        self.baseline_path = baseline_path
        self.runtime_path = runtime_path
        self.allow_write = os.getenv("SCOUT_ALLOW_CONFIG_WRITE", "false").lower() == "true"
        
        # Ensure runtime directory exists
        if self.allow_write:
            os.makedirs(os.path.dirname(runtime_path), exist_ok=True)
    
    def _load_baseline(self) -> Dict[str, Any]:
        """Load baseline configuration from feeds.yaml."""
        try:
            with open(self.baseline_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # Ensure defaults
            if "default_poll_interval" not in config:
                config["default_poll_interval"] = 900
            
            if "default_notifications" not in config:
                config["default_notifications"] = {
                    "enabled": False,
                    "min_score": 8
                }
            
            if "feeds" not in config:
                config["feeds"] = []
            
            logger.info(f"Loaded baseline config: {len(config.get('feeds', []))} feeds")
            return config
        except Exception as e:
            logger.error(f"Failed to load baseline config: {e}")
            return {
                "default_poll_interval": 900,
                "default_notifications": {"enabled": False, "min_score": 8},
                "feeds": []
            }
    
    def _load_runtime(self) -> Dict[str, Any]:
        """Load runtime overrides (optional)."""
        if not os.path.exists(self.runtime_path):
            return {}
        
        try:
            with open(self.runtime_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            logger.info(f"Loaded runtime config: {len(config.get('feeds', []))} feeds")
            return config
        except Exception as e:
            logger.error(f"Failed to load runtime config: {e}")
            return {}
    
    def _save_runtime(self, config: Dict[str, Any]) -> None:
        """Save runtime overrides (only if SCOUT_ALLOW_CONFIG_WRITE=true)."""
        if not self.allow_write:
            raise PermissionError("Config write not allowed (SCOUT_ALLOW_CONFIG_WRITE=false)")
        
        try:
            with open(self.runtime_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Saved runtime config to {self.runtime_path}")
        except Exception as e:
            logger.error(f"Failed to save runtime config: {e}")
            raise
    
    def _generate_feed_id(self, feed_url: str) -> str:
        """Generate deterministic feed ID from URL."""
        return hashlib.sha256(feed_url.encode()).hexdigest()[:12]
    
    def _validate_feed(self, feed: Dict[str, Any]) -> None:
        """Validate feed configuration."""
        url = feed.get("url", "")
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid feed URL: {url}")
        
        poll_interval = feed.get("poll_interval")
        if poll_interval is not None:
            if not isinstance(poll_interval, int) or poll_interval < 60 or poll_interval > 86400:
                raise ValueError(f"poll_interval must be 60-86400 seconds, got {poll_interval}")
        
        score_threshold = feed.get("score_threshold")
        if score_threshold is not None:
            if not isinstance(score_threshold, int) or score_threshold < 1 or score_threshold > 10:
                raise ValueError(f"score_threshold must be 1-10, got {score_threshold}")
        
        notifications = feed.get("notifications")
        if notifications:
            if not isinstance(notifications, dict):
                raise ValueError("notifications must be a dict")
            if "enabled" in notifications and not isinstance(notifications["enabled"], bool):
                raise ValueError("notifications.enabled must be boolean")
            if "min_score" in notifications:
                min_score = notifications["min_score"]
                if not isinstance(min_score, int) or min_score < 1 or min_score > 10:
                    raise ValueError(f"notifications.min_score must be 1-10, got {min_score}")
    
    def get_effective_config(self) -> Dict[str, Any]:
        """
        Get effective configuration (baseline + runtime merged).
        
        Returns:
            Merged config with defaults resolved
        """
        baseline = self._load_baseline()
        runtime = self._load_runtime()
        
        # Start with baseline
        effective = {
            "default_poll_interval": baseline.get("default_poll_interval", 900),
            "default_notifications": baseline.get("default_notifications", {
                "enabled": False,
                "min_score": 8
            }),
            "feeds": []
        }
        
        # Build feed map from baseline
        baseline_feeds = {self._generate_feed_id(f.get("url", "")): f for f in baseline.get("feeds", [])}
        
        # Apply runtime overrides
        runtime_feeds = runtime.get("feeds", [])
        runtime_feed_map = {self._generate_feed_id(f.get("url", "")): f for f in runtime_feeds}
        
        # Merge: baseline feeds + runtime overrides
        all_feed_ids = set(baseline_feeds.keys()) | set(runtime_feed_map.keys())
        
        for feed_id in all_feed_ids:
            feed = baseline_feeds.get(feed_id, {}).copy()
            
            # Apply runtime override if exists
            if feed_id in runtime_feed_map:
                runtime_feed = runtime_feed_map[feed_id]
                
                # Check for tombstone (deleted)
                if runtime_feed.get("_deleted", False):
                    continue
                
                # Merge runtime overrides
                feed.update(runtime_feed)
            
            # Ensure feed has ID
            if "id" not in feed:
                feed["id"] = feed_id
            
            # Resolve defaults
            if "poll_interval" not in feed:
                feed["poll_interval"] = effective["default_poll_interval"]
            
            if "enabled" not in feed:
                feed["enabled"] = True
            
            if "notifications" not in feed:
                feed["notifications"] = effective["default_notifications"].copy()
            else:
                # Merge notification defaults
                feed_notifications = feed["notifications"].copy()
                if "enabled" not in feed_notifications:
                    feed_notifications["enabled"] = effective["default_notifications"]["enabled"]
                if "min_score" not in feed_notifications:
                    feed_notifications["min_score"] = effective["default_notifications"]["min_score"]
                feed["notifications"] = feed_notifications
            
            effective["feeds"].append(feed)
        
        return effective
    
    def add_feed(self, feed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new feed (to runtime config).
        
        Args:
            feed: Feed dict with name, url, and optional settings
            
        Returns:
            Created feed with ID
        """
        if not self.allow_write:
            raise PermissionError("Config write not allowed")
        
        # Validate
        self._validate_feed(feed)
        
        # Generate ID
        feed_id = self._generate_feed_id(feed["url"])
        
        # Check if already exists
        effective = self.get_effective_config()
        existing_ids = {f.get("id") for f in effective.get("feeds", [])}
        if feed_id in existing_ids:
            raise ValueError(f"Feed with URL {feed['url']} already exists")
        
        # Add to runtime
        runtime = self._load_runtime()
        if "feeds" not in runtime:
            runtime["feeds"] = []
        
        feed_with_id = feed.copy()
        feed_with_id["id"] = feed_id
        runtime["feeds"].append(feed_with_id)
        
        self._save_runtime(runtime)
        
        logger.info(f"Added feed: {feed.get('name')} ({feed_id})")
        return feed_with_id
    
    def update_feed(self, feed_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update feed (in runtime config).
        
        Args:
            feed_id: Feed ID
            updates: Dict with fields to update (enabled, poll_interval, score_threshold, notifications, name)
            
        Returns:
            Updated feed
        """
        if not self.allow_write:
            raise PermissionError("Config write not allowed")
        
        effective = self.get_effective_config()
        feed = None
        
        for f in effective.get("feeds", []):
            if f.get("id") == feed_id:
                feed = f.copy()
                break
        
        if not feed:
            raise ValueError(f"Feed {feed_id} not found")
        
        # Apply updates
        allowed_fields = {"enabled", "poll_interval", "score_threshold", "notifications", "name"}
        for key, value in updates.items():
            if key not in allowed_fields:
                raise ValueError(f"Cannot update field: {key}")
            feed[key] = value
        
        # Validate updated feed
        self._validate_feed(feed)
        
        # Save to runtime
        runtime = self._load_runtime()
        if "feeds" not in runtime:
            runtime["feeds"] = []
        
        # Find and update in runtime, or add if not present
        found = False
        for i, f in enumerate(runtime["feeds"]):
            if self._generate_feed_id(f.get("url", "")) == feed_id:
                runtime["feeds"][i] = feed
                found = True
                break
        
        if not found:
            runtime["feeds"].append(feed)
        
        self._save_runtime(runtime)
        
        logger.info(f"Updated feed: {feed_id}")
        return feed
    
    def delete_feed(self, feed_id: str) -> None:
        """
        Delete feed (mark as deleted in runtime).
        
        Args:
            feed_id: Feed ID
        """
        if not self.allow_write:
            raise PermissionError("Config write not allowed")
        
        effective = self.get_effective_config()
        feed = None
        
        for f in effective.get("feeds", []):
            if f.get("id") == feed_id:
                feed = f
                break
        
        if not feed:
            raise ValueError(f"Feed {feed_id} not found")
        
        # Mark as deleted in runtime
        runtime = self._load_runtime()
        if "feeds" not in runtime:
            runtime["feeds"] = []
        
        # Check if already in runtime
        found = False
        for i, f in enumerate(runtime["feeds"]):
            if self._generate_feed_id(f.get("url", "")) == feed_id:
                runtime["feeds"][i]["_deleted"] = True
                found = True
                break
        
        if not found:
            # Add tombstone
            tombstone = feed.copy()
            tombstone["_deleted"] = True
            runtime["feeds"].append(tombstone)
        
        self._save_runtime(runtime)
        
        logger.info(f"Deleted feed: {feed_id}")


# Global instance
config_store = ConfigStore()

