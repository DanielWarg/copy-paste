"""Privacy-safe structured JSON logging.

NO payloads, NO headers, NO PII in logs.
Only: request_id, path, method, status_code, latency_ms.
"""
import json
import logging
import random
import sys
from typing import Any, Dict

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for privacy-safe logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms

        # Add any extra fields from extra dict (but filter forbidden keys)
        if hasattr(record, "extra_data"):
            extra = record.extra_data
            # Filter out forbidden keys (dynamic based on SOURCE_SAFETY_MODE)
            forbidden_keys = _get_forbidden_log_keys()
            safe_extra = {
                k: v
                for k, v in extra.items()
                if k.lower() not in forbidden_keys
            }
            log_data.update(safe_extra)

        # Final privacy-safe assertion
        _assert_privacy_safe(log_data)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    """Configure structured JSON logging.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    # Set formatter based on config
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def should_log() -> bool:
    """Check if request should be logged based on sample rate.

    Returns:
        True if request should be logged, False otherwise.
    """
    return random.random() < settings.log_sample_rate


# Forbidden keys that must NEVER appear in logs (privacy-safe enforcement)
# Base set (always forbidden)
_BASE_FORBIDDEN_LOG_KEYS = frozenset({
    "authorization",
    "cookie",
    "body",
    "payload",
    "headers",
    "query_params",
    "query",
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
})

# Source protection keys (forbidden when SOURCE_SAFETY_MODE is enabled)
_SOURCE_PROTECTION_KEYS = frozenset({
    "user-agent",
    "user_agent",
    "ip",
    "ip_address",
    "client_ip",
    "remote_addr",
    "x-forwarded-for",
    "x-real-ip",
    "referer",
    "referrer",
    "origin",
    "url",
    "uri",
    "filename",
    "filepath",
    "file_path",
    "original_filename",
    "querystring",
    "query_string",
    "cookies",
    "host",
    "hostname",
})

# Dynamic forbidden keys (depends on SOURCE_SAFETY_MODE)
def _get_forbidden_log_keys() -> frozenset:
    """Get forbidden log keys based on SOURCE_SAFETY_MODE setting."""
    if settings.source_safety_mode:
        return _BASE_FORBIDDEN_LOG_KEYS | _SOURCE_PROTECTION_KEYS
    return _BASE_FORBIDDEN_LOG_KEYS

# For backward compatibility, use function call
_FORBIDDEN_LOG_KEYS = _get_forbidden_log_keys()


def _assert_privacy_safe(log_data: Dict[str, Any]) -> None:
    """Assert that log data contains no forbidden keys (privacy-safe check).

    Args:
        log_data: Log data dictionary to check

    Raises:
        AssertionError: If forbidden keys are found
    """
    keys_lower = {k.lower() for k in log_data.keys()}
    forbidden_keys = _get_forbidden_log_keys()
    forbidden_found = keys_lower & forbidden_keys
    if forbidden_found:
        raise AssertionError(
            f"Privacy violation: forbidden keys found in log: {forbidden_found}"
        )


def log_request(
    logger: logging.Logger,
    request_id: str,
    path: str,
    method: str,
    status_code: int,
    latency_ms: float,
) -> None:
    """Log HTTP request with privacy-safe structured data.

    Args:
        logger: Logger instance
        request_id: Request ID
        path: Request path
        method: HTTP method
        status_code: HTTP status code
        latency_ms: Request latency in milliseconds
    """
    if not should_log():
        return

    # Build log data with ONLY allowed fields
    log_data = {
        "request_id": request_id,
        "path": path,
        "method": method,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
    }

    # Assert privacy-safe (raises if forbidden keys found)
    _assert_privacy_safe(log_data)

    logger.info("http_request", extra=log_data)


def log_privacy_safe(event_id: str, message: str, **kwargs: Any) -> None:
    """
    Log privacy-safe information only (convenience function for privacy modules).
    
    Args:
        event_id: Event identifier
        message: Log message
        **kwargs: Additional privacy-safe metrics (no PII allowed)
    """
    logger = logging.getLogger("app")
    safe_data = {
        "event_id": event_id,
        **{k: v for k, v in kwargs.items() if k.lower() not in _get_forbidden_log_keys()}
    }
    logger.info(message, extra=safe_data)


# Initialize logger
logger = setup_logging()
