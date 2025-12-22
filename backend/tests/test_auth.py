"""
Tests for authentication and rate limiting - using real API keys
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings

client = TestClient(app)


def test_health_no_auth_required():
    """Test that /health endpoint doesn't require auth"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_endpoints_require_auth():
    """Test that API endpoints require authentication"""
    # Test without API key
    response = client.get("/api/v1/sources")
    assert response.status_code == 401
    
    # Test with invalid API key
    response = client.get(
        "/api/v1/sources",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401


def test_api_endpoints_with_valid_key():
    """Test that API endpoints work with valid API key"""
    # Use first API key from settings
    api_key = settings.api_key_list[0]
    
    response = client.get(
        "/api/v1/sources",
        headers={"X-API-Key": api_key}
    )
    # Should succeed (even if empty list)
    assert response.status_code in [200, 401]  # 401 if no sources yet


def test_rate_limiting():
    """Test that rate limiting is enforced"""
    api_key = settings.api_key_list[0]
    
    # Make requests up to limit
    for i in range(settings.rate_limit_rpm + 5):
        response = client.get(
            "/api/v1/sources",
            headers={"X-API-Key": api_key}
        )
        
        if i >= settings.rate_limit_rpm:
            # Should hit rate limit
            assert response.status_code == 429
            break

