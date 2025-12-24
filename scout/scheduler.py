"""
Scheduler - Manages RSS feed polling with APScheduler.

Supports:
- Configurable polling intervals per feed
- Feed enabled/disabled state
- Exponential backoff for failed feeds
- SCOUT_RUN_ONCE flag for demo/CI
"""
import os
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Dict
try:
    from scout.rss_watcher import RSSWatcher
    from scout.api import app
    from scout.config_store import config_store
except ImportError:
    # For relative imports when running as module
    from rss_watcher import RSSWatcher
    from api import app
    from config_store import config_store
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeedScheduler:
    """
    Manages RSS feed polling with backoff and error handling.
    """
    
    def __init__(self, backend_url: str, feeds_config_path: str = "feeds.yaml"):
        """
        Initialize scheduler.
        
        Args:
            backend_url: Backend API URL
            feeds_config_path: Path to feeds.yaml
        """
        self.backend_url = backend_url
        self.feeds_config_path = feeds_config_path
        self.watcher = RSSWatcher(backend_url, feeds_config_path)
        self.scheduler = AsyncIOScheduler()
        self.feed_failures: Dict[str, int] = {}  # Track failures per feed
        self.feed_backoff: Dict[str, int] = {}  # Track backoff intervals
    
    def _get_poll_interval(self, feed_config: Dict) -> int:
        """
        Get poll interval for a feed (per feed or default).
        
        Args:
            feed_config: Feed configuration
            
        Returns:
            Poll interval in seconds
        """
        if "poll_interval" in feed_config:
            return feed_config["poll_interval"]
        
        effective_config = config_store.get_effective_config()
        default = effective_config.get("default_poll_interval", 900)
        return default
    
    def _calculate_backoff(self, feed_name: str) -> int:
        """
        Calculate exponential backoff interval.
        
        Args:
            feed_name: Name of the feed
            
        Returns:
            Backoff interval in seconds
        """
        failures = self.feed_failures.get(feed_name, 0)
        
        if failures == 0:
            return 0
        
        # Exponential backoff: 2^failures minutes, max 60 minutes
        backoff_minutes = min(2 ** failures, 60)
        return backoff_minutes * 60
    
    async def _poll_feed_with_backoff(self, feed_config: Dict) -> None:
        """
        Poll a feed with backoff handling.
        
        Args:
            feed_config: Feed configuration
        """
        feed_name = feed_config.get("name", feed_config.get("url", "unknown"))
        
        # Check backoff
        backoff_seconds = self._calculate_backoff(feed_name)
        if backoff_seconds > 0:
            logger.warning(f"Feed {feed_name} in backoff ({backoff_seconds}s), skipping")
            return
        
        try:
            new_items = await self.watcher.poll_feed(feed_config)
            
            # Reset failures on success
            if new_items >= 0:
                self.feed_failures[feed_name] = 0
                self.feed_backoff[feed_name] = 0
        except Exception as e:
            # Increment failures
            self.feed_failures[feed_name] = self.feed_failures.get(feed_name, 0) + 1
            failures = self.feed_failures[feed_name]
            
            logger.error(f"Error polling {feed_name}: {e} (failures: {failures})")
            
            # Max 10 failures → permanent backoff
            if failures >= 10:
                logger.error(f"Feed {feed_name} exceeded max failures, permanent backoff")
                self.feed_backoff[feed_name] = 3600  # 1 hour
    
    def _reload_and_reschedule(self) -> None:
        """Reload effective config and reschedule feeds."""
        effective_config = config_store.get_effective_config()
        feeds = effective_config.get("feeds", [])
        
        # Remove all existing jobs
        self.scheduler.remove_all_jobs()
        
        for feed_config in feeds:
            if not feed_config.get("enabled", True):
                logger.debug(f"Skipping disabled feed: {feed_config.get('name')}")
                continue
            
            feed_id = feed_config.get("id", "unknown")
            feed_name = feed_config.get("name", feed_config.get("url", "unknown"))
            poll_interval = self._get_poll_interval(feed_config)
            
            # Schedule polling job
            self.scheduler.add_job(
                self._poll_feed_with_backoff,
                trigger=IntervalTrigger(seconds=poll_interval),
                args=[feed_config],
                id=f"feed_{feed_id}",
                replace_existing=True
            )
            
            logger.info(f"Scheduled feed {feed_name} ({feed_id}) with interval {poll_interval}s")
    
    def start(self) -> None:
        """Start scheduler with all enabled feeds."""
        self._reload_and_reschedule()
        self.scheduler.start()
        logger.info("Scheduler started")
    
    async def run_once(self) -> None:
        """Run one polling cycle for all feeds (for SCOUT_RUN_ONCE)."""
        logger.info("Running single polling cycle (SCOUT_RUN_ONCE)")
        # Ensure watcher uses effective config
        results = await self.watcher.poll_all_feeds()
        
        total = sum(results.values())
        logger.info(f"Single cycle complete: {total} new items across {len(results)} feeds")
    
    def stop(self) -> None:
        """Stop scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")


async def run_scheduler_loop(scheduler: FeedScheduler):
    """Run scheduler polling loop with config reload."""
    scheduler.start()
    
    try:
        reload_counter = 0
        while True:
            await asyncio.sleep(60)
            reload_counter += 1
            
            # Reload config every 60 seconds
            if reload_counter >= 1:
                logger.debug("Reloading feed configuration...")
                scheduler._reload_and_reschedule()
                reload_counter = 0
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down scheduler...")
        scheduler.stop()


async def main():
    """Main entry point."""
    backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
    feeds_config = os.getenv("FEEDS_CONFIG", "feeds.yaml")
    run_once = os.getenv("SCOUT_RUN_ONCE", "false").lower() == "true"
    
    scheduler = FeedScheduler(backend_url, feeds_config)
    
    if run_once:
        # Run once and exit
        await scheduler.run_once()
        return
    
    # Start scheduler in background task
    scheduler_task = asyncio.create_task(run_scheduler_loop(scheduler))
    
    # #region agent log
    import json
    from datetime import datetime
    log_path = "/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE/.cursor/debug.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            log_entry = {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "location": "scout/scheduler.py:210",
                "message": "Before uvicorn server start",
                "data": {
                    "app_id": id(app),
                    "middleware_count": len(app.user_middleware),
                    "middleware_types": [str(type(m.cls)) for m in app.user_middleware]
                },
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A"
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion
    
    # Start API server (for /scout/events endpoint)
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
        scheduler.stop()
        scheduler_task.cancel()
        await scheduler_task


if __name__ == "__main__":
    asyncio.run(main())

