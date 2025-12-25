"""Egress Control - Code-level enforcement of no external egress in prod_brutal profile.

CRITICAL: All external providers MUST call ensure_egress_allowed() before making
any network requests to external services.

Policy:
- In prod_brutal profile: ALL external egress is blocked (fail-closed)
- In dev/test: egress is allowed (for development)
"""
import os
from app.core.config import settings
from app.core.logging import logger


class EgressBlockedError(Exception):
    """Raised when egress is blocked in prod_brutal profile."""
    pass


def ensure_egress_allowed() -> None:
    """
    Ensure external egress is allowed.
    
    Policy:
    - If ENVIRONMENT=production AND PROFILE=prod_brutal: BLOCK (raise EgressBlockedError)
    - Otherwise: ALLOW (no-op)
    
    This is a code-level kill switch that complements infrastructure-level
    egress blocking (internal docker network).
    
    Raises:
        EgressBlockedError: If egress is blocked in prod_brutal profile
    """
    environment = os.getenv("ENVIRONMENT", "").lower()
    profile = os.getenv("PROFILE", "").lower()
    
    if environment == "production" and profile == "prod_brutal":
        logger.error(
            "egress_blocked",
            extra={
                "error_type": "EgressBlockedError",
                "policy_code": "prod_brutal_no_egress"
            }
        )
        raise EgressBlockedError(
            "External egress is blocked in prod_brutal profile. "
            "All external API calls must be disabled in production."
        )
    
    # In dev/test, egress is allowed (no-op)
    return

