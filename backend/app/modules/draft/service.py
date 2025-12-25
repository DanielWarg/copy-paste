"""Draft Service - Draft generation with provider abstraction."""
from datetime import datetime
from typing import Optional

from app.modules.draft.models import DraftResponse
from app.modules.draft.providers.stub_provider import stub_provider


async def create_draft(
    event_id: int,
    masked_text: str,  # CRITICAL: Only masked text (no raw PII)
    request_id: str
) -> DraftResponse:
    """
    Create draft for event using masked text.
    
    CRITICAL: This function ONLY accepts masked_text (already passed through privacy_gate).
    No raw text should ever reach this function.
    
    Args:
        event_id: Event ID
        masked_text: Masked text (guaranteed no direct PII)
        request_id: Request ID for tracking
        
    Returns:
        DraftResponse
        
    Raises:
        ValueError: If event not found
    """
    # For now, we accept any event_id (stub implementation)
    # In real implementation, verify event exists by querying database/console module
    # For testing purposes, we'll accept any event_id and generate draft
    
    # Generate draft using provider (stub for now)
    draft_content = await stub_provider.generate_draft(
        event_id=event_id,
        masked_text=masked_text,
        request_id=request_id
    )
    
    # Create draft response
    # TODO: Store draft in database (for now, just return)
    draft_id = 1  # Stub ID
    
    return DraftResponse(
        draft_id=draft_id,
        event_id=event_id,
        content=draft_content,
        created_at=datetime.now().isoformat()
    )

