"""LLaMA.cpp Provider - Advisory control check via OpenAI-compatible endpoint."""
import httpx
from typing import Optional, Dict
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import logger
from app.modules.privacy_shield.models import MaskedPayload


class LLaMACppProvider:
    """LLaMA.cpp provider for advisory control checks."""
    
    def __init__(self):
        """Initialize LLaMA.cpp provider."""
        self.base_url = settings.llamacpp_base_url
        self.client: Optional[httpx.AsyncClient] = None
        self._enabled = False
        
        if self.base_url:
            self._enabled = True
            self.client = httpx.AsyncClient(timeout=settings.privacy_timeout_seconds)
    
    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self._enabled
    
    async def control_check(self, masked_payload: MaskedPayload) -> Dict[str, any]:
        """
        Run advisory control check on masked text.
        
        Args:
            masked_payload: MaskedPayload instance
            
        Returns:
            Dict with control check result: {"ok": bool, "reasons": List[str]}
            
        Raises:
            HTTPException: If provider not enabled or request fails
        """
        if not self._enabled or not self.client:
            return {"ok": True, "reasons": []}  # No check = OK (advisory)
        
        try:
            # Call LLaMA.cpp OpenAI-compatible endpoint
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": "control",  # Default model name
                    "messages": [
                        {
                            "role": "system",
                            "content": "Check if the following text contains any direct identifiers (email, phone, personal number, address). Respond with JSON: {\"ok\": true/false, \"reasons\": [...]}"
                        },
                        {
                            "role": "user",
                            "content": masked_payload.text[:1000]  # Limit context
                        }
                    ],
                    "max_tokens": 100
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse response (basic - could be improved)
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # Try to parse JSON response
            import json
            try:
                parsed = json.loads(content)
                return {
                    "ok": parsed.get("ok", True),
                    "reasons": parsed.get("reasons", [])
                }
            except json.JSONDecodeError:
                # If JSON parse fails, assume OK (advisory check)
                return {"ok": True, "reasons": []}
                
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(
                "llamacpp_control_check_failed",
                extra={
                    "request_id": masked_payload.request_id,
                    "error_type": error_type
                }
            )
            # Advisory check failure = OK (non-blocking)
            return {"ok": True, "reasons": []}
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()


# Global instance
llamacpp_provider = LLaMACppProvider()

