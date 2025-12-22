"""
SSRF-protected URL fetcher
"""
import httpx
from typing import Optional
from urllib.parse import urlparse
from ..core.config import settings
from ..core.security import validate_url_scheme, is_private_ip, is_metadata_endpoint


class SSRFError(Exception):
    """Raised when SSRF protection blocks a request"""
    pass


class URLFetcher:
    """SSRF-protected URL fetcher"""
    
    MAX_RESPONSE_SIZE = settings.max_upload_mb * 1024 * 1024  # Convert MB to bytes
    TIMEOUT = 30.0  # seconds
    MAX_REDIRECTS = 5
    
    async def fetch(self, url: str) -> tuple[str, bytes]:
        """
        Fetch URL content with SSRF protection
        
        Returns:
            tuple: (content_type, content_bytes)
        
        Raises:
            SSRFError: If URL is blocked by SSRF protection
        """
        # Validate scheme
        if not validate_url_scheme(url):
            raise SSRFError(f"Only HTTPS URLs are allowed, got: {url}")
        
        # Parse URL
        parsed = urlparse(url)
        host = parsed.hostname
        
        # Block private IPs
        if is_private_ip(host):
            raise SSRFError(f"Private IP addresses are blocked: {host}")
        
        # Block metadata endpoints
        if is_metadata_endpoint(host):
            raise SSRFError(f"Metadata endpoints are blocked: {host}")
        
        # Fetch with limits
        async with httpx.AsyncClient(
            timeout=self.TIMEOUT,
            follow_redirects=True,
            max_redirects=self.MAX_REDIRECTS,
        ) as client:
            async with client.stream("GET", url) as response:
                # Check content length header if present
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.MAX_RESPONSE_SIZE:
                    raise SSRFError(
                        f"Response too large: {content_length} bytes "
                        f"(max: {self.MAX_RESPONSE_SIZE} bytes)"
                    )
                
                # Read content with size limit
                content = b""
                async for chunk in response.aiter_bytes():
                    content += chunk
                    if len(content) > self.MAX_RESPONSE_SIZE:
                        raise SSRFError(
                            f"Response exceeds size limit: {len(content)} bytes "
                            f"(max: {self.MAX_RESPONSE_SIZE} bytes)"
                        )
                
                # Get content type
                content_type = response.headers.get("content-type", "text/plain")
                
                return content_type, content

