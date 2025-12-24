"""Global exception handlers for consistent error responses.

Privacy-safe: No stacktraces, no headers, no bodies in production.
Always includes request_id for traceability.
"""
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings


def get_request_id(request: Request) -> str:
    """Get request ID from request state, or generate one if missing.

    Args:
        request: FastAPI request

    Returns:
        Request ID string
    """
    if hasattr(request.state, "request_id"):
        return str(request.state.request_id)
    # Fallback: generate a simple ID (should not happen if middleware is working)
    import uuid

    return str(uuid.uuid4())


def create_error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int = 500,
    debug_details: Optional[str] = None,
) -> JSONResponse:
    """Create a consistent error response.

    Args:
        request: FastAPI request
        code: Error code (e.g., "internal_error", "http_error", "validation_error")
        message: Human-readable error message
        status_code: HTTP status code
        debug_details: Optional debug details (only included if DEBUG=true)

    Returns:
        JSONResponse with error shape
    """
    request_id = get_request_id(request)

    error_data: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }

    # Add debug details only if DEBUG is enabled
    if settings.debug and debug_details:
        error_data["error"]["debug"] = debug_details

    return JSONResponse(
        status_code=status_code,
        content=error_data,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTPException (FastAPI/Starlette).

    Args:
        request: FastAPI request
        exc: HTTPException

    Returns:
        JSONResponse with error shape
    """
    # Use generic message in production, actual detail in debug
    if settings.debug:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error occurred"
    else:
        message = "Request failed"

    return create_error_response(
        request=request,
        code="http_error",
        message=message,
        status_code=exc.status_code,
        debug_details=str(exc.detail) if settings.debug and exc.detail else None,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle RequestValidationError (Pydantic validation).

    Args:
        request: FastAPI request
        exc: RequestValidationError

    Returns:
        JSONResponse with error shape
    """
    # Use generic message in production, actual errors in debug
    if settings.debug:
        # Extract validation errors (safe - no headers/body)
        errors = exc.errors()
        debug_details = f"Validation failed: {len(errors)} error(s)"
    else:
        debug_details = None

    return create_error_response(
        request=request,
        code="validation_error",
        message="Invalid request" if not settings.debug else "Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        debug_details=debug_details,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions (fallback 500).

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSONResponse with error shape
    """
    # Log the exception (privacy-safe logging handles this)
    from app.core.logging import logger

    request_id = get_request_id(request)
    logger.error(
        "unhandled_exception",
        extra={
            "request_id": request_id,
            "path": str(request.url.path),
            "method": request.method,
            "error_type": type(exc).__name__,
        },
    )

    # Never expose exception details in production
    if settings.debug:
        debug_details = f"{type(exc).__name__}: {str(exc)}"
    else:
        debug_details = None

    return create_error_response(
        request=request,
        code="internal_error",
        message="Internal error" if not settings.debug else "An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        debug_details=debug_details,
    )

