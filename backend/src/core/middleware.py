"""
Middleware for authentication, rate limiting, and audit
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import time
from collections import defaultdict
from ..core.config import settings
import uuid


# Rate limiting storage (in-memory for now, use Redis in production)
rate_limit_store: dict[str, list[float]] = defaultdict(list)
concurrency_tracker: dict[str, int] = defaultdict(int)


class APIKeyAuth(HTTPBearer):
    """API Key authentication"""
    
    async def __call__(self, request: Request) -> Optional[str]:
        """Extract and validate API key"""
        # Try header first
        api_key = request.headers.get(settings.api_key_header)
        
        if not api_key:
            # Try Authorization header as fallback
            credentials = await super().__call__(request)
            if credentials:
                api_key = credentials.credentials
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
        
        # Validate API key
        if api_key not in settings.api_key_list:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return api_key


def check_rate_limit(api_key: str) -> None:
    """Check and enforce rate limiting"""
    now = time.time()
    minute_ago = now - 60
    
    # Clean old entries
    rate_limit_store[api_key] = [
        timestamp for timestamp in rate_limit_store[api_key]
        if timestamp > minute_ago
    ]
    
    # Check limit
    if len(rate_limit_store[api_key]) >= settings.rate_limit_rpm:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {settings.rate_limit_rpm} requests per minute"
        )
    
    # Record request
    rate_limit_store[api_key].append(now)


def check_concurrency(api_key: str) -> None:
    """Check and enforce concurrency limits"""
    if concurrency_tracker[api_key] >= settings.llm_concurrency:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Concurrency limit exceeded: {settings.llm_concurrency} concurrent LLM calls"
        )


def increment_concurrency(api_key: str) -> None:
    """Increment concurrency counter"""
    concurrency_tracker[api_key] += 1


def decrement_concurrency(api_key: str) -> None:
    """Decrement concurrency counter"""
    if concurrency_tracker[api_key] > 0:
        concurrency_tracker[api_key] -= 1


def generate_trace_id() -> str:
    """Generate trace ID for request tracking"""
    return str(uuid.uuid4())

