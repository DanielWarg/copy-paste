"""
Security utilities: hashing, validation, etc.
"""
import hashlib
from typing import Optional


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def validate_url_scheme(url: str) -> bool:
    """Validate URL scheme is allowed (https only)"""
    return url.startswith("https://")


def is_private_ip(host: str) -> bool:
    """Check if host is a private IP address"""
    if not host:
        return False
    
    # Remove port if present
    host = host.split(':')[0]
    
    # Check for private IP ranges
    if host.startswith("127.") or host.startswith("192.168.") or host.startswith("10."):
        return True
    
    # Check for link-local (169.254.x.x)
    if host.startswith("169.254."):
        return True
    
    # Check for localhost variants
    if host in ("localhost", "::1", "0.0.0.0"):
        return True
    
    return False


def is_metadata_endpoint(host: str) -> bool:
    """Check if host is a metadata endpoint (cloud metadata services)"""
    if not host:
        return False
    
    host = host.split(':')[0]
    
    # AWS metadata endpoint
    if host == "169.254.169.254":
        return True
    
    # Common metadata hostnames
    metadata_hosts = [
        "metadata.google.internal",
        "metadata.azure.com",
        "169.254.169.254",
    ]
    
    return host.lower() in [h.lower() for h in metadata_hosts]

