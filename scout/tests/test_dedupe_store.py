"""
Tests for dedupe_store.py
"""
import os
import tempfile
import pytest
from dedupe_store import DedupeStore
from uuid import uuid4


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    store = DedupeStore(db_path=db_path)
    yield store
    
    # Cleanup
    os.unlink(db_path)


def test_is_seen_false(temp_db):
    """Test is_seen returns False for unseen key."""
    assert temp_db.is_seen("test_key_123") is False


def test_mark_seen(temp_db):
    """Test marking key as seen."""
    event_id = uuid4()
    temp_db.mark_seen("test_key_123", "https://example.com/feed", event_id)
    assert temp_db.is_seen("test_key_123") is True


def test_get_recent_events(temp_db):
    """Test getting recent events."""
    event_id = uuid4()
    temp_db.mark_seen("test_key_123", "https://example.com/feed", event_id)
    
    events = temp_db.get_recent_events(hours=24)
    assert len(events) == 1
    assert events[0]["dedupe_key"] == "test_key_123"
    assert events[0]["event_id"] == str(event_id)


def test_cleanup_old(temp_db):
    """Test cleanup of old items."""
    event_id = uuid4()
    temp_db.mark_seen("test_key_123", "https://example.com/feed", event_id)
    
    removed = temp_db.cleanup_old(days=0)  # Remove all
    assert removed >= 0
    
    assert temp_db.is_seen("test_key_123") is False

