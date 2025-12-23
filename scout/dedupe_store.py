"""
Deduplication Store - SQLite-based storage for seen RSS items.

GDPR: Lagrar endast dedupe-key och event_id, aldrig innehåll.
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class DedupeStore:
    """
    Manages deduplication of RSS items using SQLite.
    
    Stores only dedupe-key and event_id - never content.
    """
    
    def __init__(self, db_path: str = "data/dedupe.db"):
        """
        Initialize dedupe store.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seen_items (
                dedupe_key TEXT PRIMARY KEY,
                feed_id TEXT,
                feed_url TEXT NOT NULL,
                event_id TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                score INTEGER,
                notification_sent INTEGER DEFAULT 0
            )
        """)
        
        # Migration: Add new columns if they don't exist (for existing DBs)
        try:
            cursor.execute("ALTER TABLE seen_items ADD COLUMN feed_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE seen_items ADD COLUMN detected_at TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE seen_items ADD COLUMN score INTEGER")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE seen_items ADD COLUMN notification_sent INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        # Migrate existing first_seen to detected_at if needed
        try:
            cursor.execute("UPDATE seen_items SET detected_at = first_seen WHERE detected_at IS NULL")
        except sqlite3.OperationalError:
            pass  # first_seen column may not exist
        
        # Index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feed_url ON seen_items(feed_url)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feed_id ON seen_items(feed_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detected_at ON seen_items(detected_at)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Dedupe store initialized at {self.db_path}")
    
    def is_seen(self, dedupe_key: str) -> bool:
        """
        Check if dedupe_key has been seen before.
        
        Args:
            dedupe_key: Dedupe key to check
            
        Returns:
            True if seen, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM seen_items WHERE dedupe_key = ?",
            (dedupe_key,)
        )
        
        result = cursor.fetchone() is not None
        conn.close()
        
        return result
    
    def mark_seen(
        self,
        dedupe_key: str,
        feed_id: str,
        feed_url: str,
        event_id: UUID,
        detected_at: str,
        score: Optional[int] = None
    ) -> None:
        """
        Mark dedupe_key as seen.
        
        Args:
            dedupe_key: Dedupe key to mark
            feed_id: Feed ID (hash of URL)
            feed_url: RSS feed URL
            event_id: Event ID from backend
            detected_at: ISO timestamp string
            score: Optional score (1-10)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or update (update if exists)
        cursor.execute("""
            INSERT INTO seen_items (dedupe_key, feed_id, feed_url, event_id, detected_at, score)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(dedupe_key) DO UPDATE SET
                event_id = ?,
                detected_at = ?,
                score = ?
        """, (dedupe_key, feed_id, feed_url, str(event_id), detected_at, score, str(event_id), detected_at, score))
        
        conn.commit()
        conn.close()
    
    def mark_notified(self, event_id: str) -> None:
        """
        Mark event as notification sent.
        
        Args:
            event_id: Event ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE seen_items
            SET notification_sent = 1
            WHERE event_id = ?
        """, (event_id,))
        
        conn.commit()
        conn.close()
    
    def cleanup_old(self, days: int = 30) -> int:
        """
        Remove items older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of items removed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cursor.execute(
            "DELETE FROM seen_items WHERE first_seen < ?",
            (cutoff_date,)
        )
        
        removed = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {removed} old items (older than {days} days)")
        return removed
    
    def get_recent_events(
        self,
        hours: int = 24,
        min_score: Optional[int] = None,
        limit: int = 50
    ) -> list:
        """
        Get recent events for UI display.
        
        Args:
            hours: Number of hours to look back
            min_score: Optional minimum score filter
            limit: Maximum number of events to return
            
        Returns:
            List of dicts with event_id, feed_id, feed_url, detected_at, score, notification_sent
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        query = """
            SELECT event_id, feed_id, feed_url, detected_at, score, notification_sent
            FROM seen_items
            WHERE detected_at >= ?
        """
        params = [cutoff_str]
        
        if min_score is not None:
            query += " AND score >= ?"
            params.append(min_score)
        
        query += " ORDER BY detected_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "event_id": row["event_id"],
                "feed_id": row["feed_id"],
                "feed_url": row["feed_url"],
                "detected_at": row["detected_at"],
                "score": row["score"],
                "notification_sent": bool(row["notification_sent"])
            }
            for row in rows
        ]
    
    def get_event_by_id(self, event_id: str) -> Optional[dict]:
        """
        Get event by event_id.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event dict or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_id, feed_id, feed_url, detected_at, score, notification_sent
            FROM seen_items
            WHERE event_id = ?
        """, (event_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "event_id": row["event_id"],
                "feed_id": row["feed_id"],
                "feed_url": row["feed_url"],
                "detected_at": row["detected_at"],
                "score": row["score"],
                "notification_sent": bool(row["notification_sent"])
            }
        return None


# Global instance
dedupe_store = DedupeStore()

