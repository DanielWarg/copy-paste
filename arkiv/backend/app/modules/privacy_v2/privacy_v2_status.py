"""
Privacy v2 Status Store - RAM-only TTL, never persisted.

CRITICAL: This store tracks gating status per event_id. Draft gate MUST read from here,
not guess from text. This prevents "sken-säkerhet" where someone can bypass approval.
"""
import time
from typing import Dict, Optional
from uuid import UUID
from dataclasses import dataclass


@dataclass
class PrivacyV2Status:
    """Privacy v2 status for an event."""
    verification_passed: bool
    semantic_risk: bool
    gated: bool
    approval_required: bool
    expires_at: float
    approval_token_hash: Optional[str] = None  # Hash of token, not token itself


class PrivacyV2StatusStore:
    """Manages privacy v2 status in RAM with TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default
        self._statuses: Dict[UUID, PrivacyV2Status] = {}
        self.ttl = ttl_seconds
    
    def set_status(
        self,
        event_id: UUID,
        verification_passed: bool,
        semantic_risk: bool,
        approval_required: bool,
        approval_token_hash: Optional[str] = None
    ):
        """Set privacy v2 status for event."""
        gated = not verification_passed or semantic_risk
        self._statuses[event_id] = PrivacyV2Status(
            verification_passed=verification_passed,
            semantic_risk=semantic_risk,
            gated=gated,
            approval_required=approval_required,
            approval_token_hash=approval_token_hash,
            expires_at=time.time() + self.ttl
        )
    
    def get_status(self, event_id: UUID) -> Optional[PrivacyV2Status]:
        """Get status if exists and not expired."""
        if event_id not in self._statuses:
            return None
        status = self._statuses[event_id]
        if time.time() > status.expires_at:
            self._statuses.pop(event_id, None)
            return None
        return status
    
    def is_gated(self, event_id: UUID) -> bool:
        """Check if event is gated."""
        status = self.get_status(event_id)
        return status.gated if status else False


privacy_v2_status_store = PrivacyV2StatusStore()

