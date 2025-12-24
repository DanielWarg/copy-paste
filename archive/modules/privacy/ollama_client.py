"""
Ollama Client - Local AI integration for PII detection and anonymization.

Uses Ministral 3:14B model running locally via Ollama.
"""
import httpx
from typing import Dict, List
from app.core.config import settings
from app.core.logging import log_privacy_safe


class OllamaClient:
    """Client for Ollama API (local AI)."""
    
    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama base URL (default from settings)
            model: Model name (default from settings)
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        # CRITICAL: Shorter timeout to prevent hanging - Ollama should respond quickly
        # If Ollama is not running, fail fast and use regex fallback
        self.client = httpx.AsyncClient(timeout=10.0)  # Reduced from 30s to 10s
    
    async def detect_pii(self, text: str, event_id: str) -> Dict[str, List[str]]:
        """
        Detect PII in text using local Ollama model.
        
        Args:
            text: Text to analyze
            event_id: Event identifier for logging
            
        Returns:
            Dict with detected PII types and values
            Example: {"persons": ["John Doe", "Jane Smith"], "organizations": ["Acme Corp"]}
        """
        prompt = f"""Identify all personally identifiable information (PII) in the following text.
Return ONLY a JSON object with this structure:
{{
  "persons": ["name1", "name2"],
  "organizations": ["org1", "org2"],
  "emails": ["email1"],
  "phone_numbers": ["phone1"],
  "addresses": ["address1"]
}}
If no PII is found, return empty arrays.

Text to analyze:
{text}

JSON:"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract JSON from response
            import json
            response_text = result.get("response", "{}")
            # Try to parse JSON (might be wrapped in markdown)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            pii_data = json.loads(response_text)
            
            log_privacy_safe(
                event_id,
                "PII detection completed",
                pii_types_found=list(pii_data.keys()),
                total_items=sum(len(v) for v in pii_data.values())
            )
            
            return pii_data
            
        except Exception as e:
            log_privacy_safe(event_id, f"PII detection error: {str(e)}")
            # Return empty dict on error - fail safe
            return {
                "persons": [],
                "organizations": [],
                "emails": [],
                "phone_numbers": [],
                "addresses": []
            }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global instance
# CRITICAL: httpx.AsyncClient() creation is fast and non-blocking
# It does NOT make network calls - only creates a client object
ollama_client = OllamaClient()

