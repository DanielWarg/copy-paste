"""
Tests for rss_watcher.py
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from rss_watcher import RSSWatcher


@pytest.fixture
def watcher():
    """Create RSSWatcher instance."""
    return RSSWatcher("http://test-backend:8000", "feeds.yaml")


def test_compute_dedupe_key_guid(watcher):
    """Test dedupe key computation with guid."""
    item = {"id": "test-guid-123", "link": "https://example.com/article"}
    key = watcher._compute_dedupe_key(item, "https://example.com/feed")
    assert key == "guid:test-guid-123"


def test_compute_dedupe_key_link(watcher):
    """Test dedupe key computation with link (no guid)."""
    item = {"link": "https://example.com/article"}
    key = watcher._compute_dedupe_key(item, "https://example.com/feed")
    assert key == "link:https://example.com/article"


def test_compute_dedupe_key_hash(watcher):
    """Test dedupe key computation with hash (no guid or link)."""
    item = {"title": "Test Title", "published": "2024-01-01"}
    key = watcher._compute_dedupe_key(item, "https://example.com/feed")
    assert key.startswith("hash:")


@pytest.mark.asyncio
async def test_post_to_ingest_success(watcher):
    """Test successful POST to ingest."""
    with patch.object(watcher.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"event_id": "test-event-id"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        event_id = await watcher._post_to_ingest("url", "https://test.com", {})
        assert event_id == "test-event-id"


@pytest.mark.asyncio
async def test_post_to_ingest_failure(watcher):
    """Test failed POST to ingest."""
    with patch.object(watcher.client, 'post', new_callable=AsyncMock) as mock_post:
        import httpx
        mock_post.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
        
        event_id = await watcher._post_to_ingest("url", "https://test.com", {})
        assert event_id is None

