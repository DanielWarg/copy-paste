"""Request middleware: ID generation, timing, security headers.

Privacy-safe: NO payloads, NO headers logged.
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import log_request, logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware for request ID generation and privacy-safe logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with ID generation, timing, and logging.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with X-Request-Id header
        """
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Add to request state
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error (no payloads)
            logger.error(
                "request_error",
                extra={
                    "request_id": request_id,
                    "path": str(request.url.path),
                    "method": request.method,
                    "error": str(e),
                },
            )
            raise

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Add request ID to response header
        response.headers["X-Request-Id"] = request_id

        # Add security headers (always set, even on errors)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store"

        # Log request (privacy-safe: no body, no headers, no client info)
        # Path is safe (no query params, no sensitive info)
        # We explicitly avoid logging: client.host, request.headers, request.url.query
        log_request(
            logger=logger,
            request_id=request_id,
            path=str(request.url.path),  # Only path, no query string
            method=request.method,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )

        return response

