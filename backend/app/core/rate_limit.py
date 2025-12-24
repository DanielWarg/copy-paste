"""
Rate Limiting - Prevent DoS attacks.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (IP address)
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def reset(self, client_id: str = None):
        """Reset rate limiter for client or all clients."""
        if client_id:
            self.requests.pop(client_id, None)
        else:
            self.requests.clear()


# Global rate limiter
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit (skip for health check)
        if request.url.path != "/health":
            if not rate_limiter.is_allowed(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later."
                )
        
        response = await call_next(request)
        return response

