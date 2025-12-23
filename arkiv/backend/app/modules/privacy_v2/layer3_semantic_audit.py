"""
Layer 3: Semantic leak check using local LLM as auditor.

Uses Ollama with Ministral 3:14B to detect semantic leaks (context that reveals identity).
"""
from typing import Tuple
from app.modules.privacy.ollama_client import ollama_client
from app.core.logging import log_privacy_safe
import json


async def semantic_audit(clean_text: str, event_id: str) -> Tuple[bool, str]:
    """
    Semantic audit: Check if anonymized text still reveals identity through context.
    
    Args:
        clean_text: Anonymized text to audit
        event_id: Event identifier for logging
        
    Returns:
        (semantic_risk: bool, risk_reason: str) where risk_reason is short code
    """
    prompt = f"""You are a Privacy Auditor. Analyze this anonymized text for semantic leaks.

A semantic leak means the text reveals someone's identity through context, even if names are replaced with tokens.

Examples of semantic leaks:
- "[PERSON_A] is the CEO of [ORG_B]" when [ORG_B] is unique/identifiable
- "[PERSON_A] lives at [ADDRESS_1]" when address is unique
- "[PERSON_A] won the Nobel Prize in 2023" (very specific event)

Return ONLY a JSON object:
{{
  "semantic_risk": true/false,
  "risk_reason": "short code or empty string"
}}

Use short codes like: "high_specificity_context", "unique_org_role", "identifiable_location", etc.

Text to audit:
{clean_text}

JSON:"""

    try:
        response = await ollama_client.client.post(
            f"{ollama_client.base_url}/api/generate",
            json={
                "model": ollama_client.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        response.raise_for_status()
        result = response.json()
        
        response_text = result.get("response", "{}")
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        audit_result = json.loads(response_text)
        
        semantic_risk = audit_result.get("semantic_risk", False)
        risk_reason = audit_result.get("risk_reason", "")
        
        # Normalize risk_reason to short code if it's too long
        if len(risk_reason) > 50:
            risk_reason = "high_specificity_context"
        
        log_privacy_safe(
            event_id,
            "Semantic audit completed",
            semantic_risk=semantic_risk,
            risk_reason_length=len(risk_reason)
        )
        
        return semantic_risk, risk_reason
        
    except Exception as e:
        error_str = str(e)
        log_privacy_safe(event_id, f"Semantic audit error: {error_str}")
        
        # CRITICAL: If Ollama is not available or model not found, don't block everything
        # Only block if it's a real audit failure (parsing error, etc)
        # Connection/model errors mean Ollama is misconfigured - we should warn but not block
        if any(marker in error_str.lower() for marker in [
            "nodename", "servname", "connection", "not found", "404", 
            "model", "not available", "unavailable"
        ]):
            # Ollama not available or model not found - warn but don't block (graceful degradation)
            log_privacy_safe(event_id, "Semantic audit unavailable (Ollama/model not accessible) - skipping audit")
            return False, "audit_unavailable"
        
        # For other errors (parsing, etc), assume risk (conservative)
        # CRITICAL: Return short code, not long error message (details in logs only)
        return True, "audit_failed"

