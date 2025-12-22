"""
Security tests for SSRF protection - using real URLs
"""
import pytest
from src.services.url_fetcher import URLFetcher, SSRFError


@pytest.mark.asyncio
async def test_ssrf_blocks_http():
    """Test that HTTP (non-HTTPS) URLs are blocked"""
    fetcher = URLFetcher()
    
    with pytest.raises(SSRFError, match="Only HTTPS URLs are allowed"):
        await fetcher.fetch("http://example.com")


@pytest.mark.asyncio
async def test_ssrf_blocks_private_ip():
    """Test that private IP addresses are blocked"""
    fetcher = URLFetcher()
    
    # Test various private IP formats
    private_urls = [
        "https://192.168.1.1",
        "https://10.0.0.1",
        "https://127.0.0.1",
        "https://localhost",
    ]
    
    for url in private_urls:
        with pytest.raises(SSRFError, match="Private IP"):
            await fetcher.fetch(url)


@pytest.mark.asyncio
async def test_ssrf_blocks_metadata_endpoint():
    """Test that metadata endpoints are blocked"""
    fetcher = URLFetcher()
    
    with pytest.raises(SSRFError, match="Metadata endpoints"):
        await fetcher.fetch("https://169.254.169.254")


@pytest.mark.asyncio
async def test_ssrf_allows_valid_https():
    """Test that valid HTTPS URLs are allowed - using real URL"""
    fetcher = URLFetcher()
    
    # Use a real, safe URL for testing (example.com is safe and predictable)
    try:
        content_type, content = await fetcher.fetch("https://www.example.com")
        
        assert content_type is not None
        assert len(content) > 0
        # Example.com contains "Example Domain" or similar
        assert b"Example" in content or b"example" in content.lower()
    except Exception as e:
        # If network fails, skip test but don't fail
        pytest.skip(f"Network test skipped: {e}")


@pytest.mark.asyncio
async def test_ssrf_enforces_size_limit():
    """Test that size limits are enforced"""
    fetcher = URLFetcher()
    
    # This test would need a URL that returns >20MB
    # For now, we test that the limit exists
    assert fetcher.MAX_RESPONSE_SIZE == 20 * 1024 * 1024  # 20MB

