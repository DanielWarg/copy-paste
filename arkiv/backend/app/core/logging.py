"""
Privacy-safe logging configuration.

Logs must NEVER contain:
- Names, addresses, phone numbers, emails
- Raw text from sources
- Mappings

Logs MAY contain:
- event_id
- Timestamps
- source_type
- Anonymized length/metrics
- External call count + cost estimate
"""
import logging
from typing import Any, Dict


def setup_logging() -> None:
    """Configure privacy-safe logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def log_privacy_safe(event_id: str, message: str, **kwargs: Any) -> None:
    """
    Log privacy-safe information only.
    
    Args:
        event_id: Event identifier
        message: Log message
        **kwargs: Additional privacy-safe metrics (no PII allowed)
    """
    logger = logging.getLogger(__name__)
    safe_data = {
        "event_id": event_id,
        **{k: v for k, v in kwargs.items() if k not in ["raw_text", "mapping", "pii"]}
    }
    logger.info(f"{message} | {safe_data}")

