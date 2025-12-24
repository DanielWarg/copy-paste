"""
Approval token manager - RAM-only TTL, never persisted.

Approval tokens are required when events are gated (verification_failed or semantic_risk).
"""
import secrets
import hashlib
import time
from typing import Dict, Optional
from uuid import UUID


class ApprovalManager:
    """Manages approval tokens in RAM with TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default
        self._tokens: Dict[str, UUID] = {}  # token -> event_id
        self._event_tokens: Dict[UUID, str] = {}  # event_id -> token
        self._timestamps: Dict[str, float] = {}
        self.ttl = ttl_seconds
    
    def generate_token(self, event_id: UUID) -> str:
        """Generate approval token for event."""
        token = secrets.token_urlsafe(32)
        self._tokens[token] = event_id
        self._event_tokens[event_id] = token
        self._timestamps[token] = time.time()
        return token
    
    def get_token_hash(self, token: str) -> str:
        """Get SHA256 hash of token (for storage in status store)."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def verify_token(self, token: str, event_id: UUID) -> bool:
        """Verify approval token matches event_id."""
        if token not in self._tokens:
            return False
        if time.time() - self._timestamps[token] > self.ttl:
            self._tokens.pop(token, None)
            self._event_tokens.pop(event_id, None)
            self._timestamps.pop(token, None)
            return False
        return self._tokens[token] == event_id
    
    def get_token_for_event(self, event_id: UUID) -> Optional[str]:
        """Get token for event if exists."""
        return self._event_tokens.get(event_id)


approval_manager = ApprovalManager()

