"""
Privacy Service - Main service for scrubbing operations.

Handles Production Mode logic and ensures is_anonymized=true for external API calls.
"""
from uuid import UUID
from fastapi import HTTPException
from app.models import StandardizedEvent, ScrubbedPayload
from app.modules.privacy.anonymizer import anonymizer
from typing import Dict
from app.core.logging import log_privacy_safe


# In-memory event store (session-based, never persisted)
_event_store: Dict[UUID, StandardizedEvent] = {}


def store_event(event: StandardizedEvent) -> None:
    """
    Store event in memory (session-based).
    
    GDPR: raw_payload is IN-MEMORY ONLY - never persisted.
    """
    _event_store[event.event_id] = event


def get_event(event_id: UUID) -> StandardizedEvent:
    """Get event from memory store."""
    if event_id not in _event_store:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_store[event_id]


async def scrub_event(
    event_id: UUID,
    production_mode: bool
) -> ScrubbedPayload:
    """
    Scrub event payload - anonymize PII.
    
    Args:
        event_id: Event identifier
        production_mode: Production Mode flag (sent in request, no global state)
        
    Returns:
        ScrubbedPayload with anonymized text
        
    Raises:
        HTTPException: If Production Mode is ON but anonymization fails (HTTP 400)
    """
    # Get event from memory
    event = get_event(event_id)
    
    # Anonymize text
    try:
        clean_text, mapping, is_anonymized = await anonymizer.anonymize(
            event.raw_payload,
            event_id,
            production_mode
        )
        
        # If production mode is ON, we MUST have is_anonymized=True
        if production_mode and not is_anonymized:
            log_privacy_safe(
                str(event_id),
                "Anonymization failed in Production Mode",
                production_mode=production_mode
            )
            raise HTTPException(
                status_code=400,
                detail="Production Mode is ON but data is not anonymized. Cannot proceed."
            )
        
        # Even in OFF mode, we should try to anonymize (but allow if it fails)
        # However, external API calls still require is_anonymized=True
        if not is_anonymized:
            # In OFF mode, we can return non-anonymized, but external APIs will still block
            log_privacy_safe(
                str(event_id),
                "Anonymization not performed (Production Mode OFF)",
                production_mode=production_mode
            )
        
        return ScrubbedPayload(
            event_id=event_id,
            clean_text=clean_text,
            is_anonymized=is_anonymized
        )
        
    except ValueError as e:
        # Anonymization failed in Production Mode
        log_privacy_safe(
            str(event_id),
            f"Anonymization error: {str(e)}",
            production_mode=production_mode
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

