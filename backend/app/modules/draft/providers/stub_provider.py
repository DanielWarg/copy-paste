"""Stub Provider - Placeholder for draft generation (no external LLM calls yet).

This provider is used to validate the draft flow without introducing external API risks.
"""
from typing import Optional


class StubProvider:
    """Stub provider for draft generation."""
    
    async def generate_draft(
        self,
        event_id: int,
        masked_text: str,
        request_id: str
    ) -> str:
        """
        Generate draft from masked text (stub implementation).
        
        Args:
            event_id: Event ID
            masked_text: Masked text (no direct PII)
            request_id: Request ID
            
        Returns:
            Stub draft content
        """
        # Stub: return dummy draft based on masked text
        # In real implementation, this would call external LLM (via privacy_gate-enforced MaskedPayload)
        return f"[DRAFT STUB] Draft for event {event_id} based on masked content (length: {len(masked_text)} chars). This is a placeholder until real LLM provider is implemented."


# Global instance
stub_provider = StubProvider()

