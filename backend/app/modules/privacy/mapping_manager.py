"""
Mapping Manager - Server RAM only, TTL-based, never persisted.

GDPR: Mapping (token → real name) must NEVER:
- Leave server RAM
- Be persisted to database
- Be included in API responses
- Be sent to external APIs
- Exist in client memory

Mapping is stored in server RAM with TTL (default 15 min), keyed by event_id.
"""
import time
from typing import Dict, Optional
from uuid import UUID
from app.core.config import settings


class MappingManager:
    """
    In-memory mapping manager with TTL.
    
    Stores mappings in server RAM only, automatically expires after TTL.
    """
    
    def __init__(self, ttl_seconds: int = None):
        """
        Initialize mapping manager.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default from settings)
        """
        self._mappings: Dict[UUID, Dict[str, str]] = {}
        self._timestamps: Dict[UUID, float] = {}
        self.ttl = ttl_seconds or settings.mapping_ttl_seconds
    
    def store(self, event_id: UUID, mapping: Dict[str, str]) -> None:
        """
        Store mapping for event_id.
        
        Args:
            event_id: Event identifier
            mapping: Token to real name mapping (e.g., {"[PERSON_A]": "John Doe"})
        """
        self._mappings[event_id] = mapping
        self._timestamps[event_id] = time.time()
    
    def get(self, event_id: UUID) -> Optional[Dict[str, str]]:
        """
        Get mapping for event_id if it exists and hasn't expired.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Mapping dict or None if not found/expired
        """
        if event_id not in self._mappings:
            return None
        
        # Check TTL
        if time.time() - self._timestamps[event_id] > self.ttl:
            self._remove(event_id)
            return None
        
        return self._mappings[event_id]
    
    def _remove(self, event_id: UUID) -> None:
        """Remove mapping for event_id."""
        self._mappings.pop(event_id, None)
        self._timestamps.pop(event_id, None)
    
    def cleanup_expired(self) -> None:
        """Remove all expired mappings."""
        current_time = time.time()
        expired = [
            event_id for event_id, timestamp in self._timestamps.items()
            if current_time - timestamp > self.ttl
        ]
        for event_id in expired:
            self._remove(event_id)
    
    def clear(self) -> None:
        """Clear all mappings (for testing)."""
        self._mappings.clear()
        self._timestamps.clear()


# Global instance (server RAM only)
mapping_manager = MappingManager()

