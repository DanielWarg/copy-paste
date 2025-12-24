"""OpenAI Provider - Hard gate for external LLM egress.

CRITICAL: Only accepts MaskedPayload, never raw str.
Runs leak_check() preflight before any network call.
"""
import httpx
from typing import Optional
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import logger
from app.modules.privacy_shield.models import MaskedPayload, PrivacyLeakError
from app.modules.privacy_shield.leak_check import check_leaks


class OpenAIProvider:
    """OpenAI provider with hard gate for privacy."""
    
    def __init__(self):
        """Initialize OpenAI provider."""
        self.base_url = "https://api.openai.com/v1"
        self.api_key = settings.openai_api_key
        self.client: Optional[httpx.AsyncClient] = None
        self._enabled = False
        
        # Start-gate: OPENAI_API_KEY must be set AND ALLOW_EXTERNAL must be True
        if self.api_key and settings.allow_external:
            self._enabled = True
            self.client = httpx.AsyncClient(timeout=settings.privacy_timeout_seconds)
        elif self.api_key and not settings.allow_external:
            logger.warning(
                "openai_provider_disabled",
                extra={
                    "reason": "ALLOW_EXTERNAL not enabled",
                    "error_type": "ConfigurationError"
                }
            )
        else:
            logger.info("openai_provider_not_configured", extra={"reason": "No API key"})
    
    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self._enabled
    
    async def generate(
        self,
        masked_payload: MaskedPayload,  # Type-safe: only MaskedPayload allowed
        prompt: str,
        model: str = "gpt-4o-mini"
    ) -> str:
        """
        Generate text using OpenAI API.
        
        CRITICAL: Only accepts MaskedPayload, never raw str.
        
        Args:
            masked_payload: MaskedPayload instance (type-safe guarantee)
            prompt: Prompt text
            model: Model name
            
        Returns:
            Generated text
            
        Raises:
            HTTPException: If provider not enabled or leak check fails
            PrivacyLeakError: If leaks detected in masked text
        """
        if not self._enabled:
            raise HTTPException(
                status_code=503,
                detail="OpenAI provider not enabled (ALLOW_EXTERNAL=false or no API key)"
            )
        
        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="OpenAI provider not initialized"
            )
        
        # Preflight leak check (hard gate)
        try:
            check_leaks(masked_payload.text, mode="strict")
        except PrivacyLeakError as e:
            logger.error(
                "openai_provider_leak_detected",
                extra={
                    "request_id": masked_payload.request_id,
                    "error_type": type(e).__name__,
                    "error_code": e.error_code
                }
            )
            raise HTTPException(
                status_code=422,
                detail="Privacy leak detected in masked text - request blocked"
            )
        
        # Make API call
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": masked_payload.text}
                    ],
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            error_type = type(e).__name__
            logger.error(
                "openai_provider_request_failed",
                extra={
                    "request_id": masked_payload.request_id,
                    "error_type": error_type
                }
            )
            raise HTTPException(
                status_code=502,
                detail="OpenAI API request failed"
            )
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()


# Global instance
openai_provider = OpenAIProvider()

