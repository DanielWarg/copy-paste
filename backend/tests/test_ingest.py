"""
Integration tests for ingest endpoint - using real URLs
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings

client = TestClient(app)


@pytest.fixture
def api_key():
    """Get a valid API key for testing"""
    return settings.api_key_list[0]


def test_ingest_valid_url(api_key):
    """Test ingesting a valid HTTPS URL"""
    response = client.post(
        "/api/v1/ingest",
        headers={"X-API-Key": api_key},
        json={
            "url": "https://www.example.com",
            "source_type": "url"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "source_id" in data


def test_ingest_invalid_scheme(api_key):
    """Test that HTTP URLs are rejected"""
    response = client.post(
        "/api/v1/ingest",
        headers={"X-API-Key": api_key},
        json={
            "url": "http://example.com",
            "source_type": "url"
        }
    )
    
    assert response.status_code == 400
    assert "HTTPS" in response.json()["detail"] or "SSRF" in response.json()["detail"]


def test_ingest_private_ip(api_key):
    """Test that private IPs are rejected"""
    response = client.post(
        "/api/v1/ingest",
        headers={"X-API-Key": api_key},
        json={
            "url": "https://192.168.1.1",
            "source_type": "url"
        }
    )
    
    assert response.status_code == 400
    assert "private" in response.json()["detail"].lower() or "SSRF" in response.json()["detail"]

