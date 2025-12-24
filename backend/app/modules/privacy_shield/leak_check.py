"""Leak check - Blocking preflight to detect remaining PII after masking."""
from typing import Dict
from app.modules.privacy_shield.regex_mask import regex_masker
from app.modules.privacy_shield.models import PrivacyLeakError


def check_leaks(text: str, mode: str = "balanced") -> None:
    """
    Check for remaining PII leaks in masked text (blocking).
    
    Args:
        text: Masked text to check
        mode: "strict" or "balanced"
        
    Raises:
        PrivacyLeakError: If leaks detected
    """
    leaks = regex_masker.count_leaks(text)
    
    # Exclude tokens from leak detection (they are safe)
    # Tokens like [EMAIL], [PHONE], [PNR] are not leaks
    safe_tokens = ["[EMAIL]", "[PHONE]", "[PNR]", "[ID]", "[POSTCODE]", "[ADDRESS]"]
    text_lower = text.lower()
    
    # Filter out leaks that are actually just tokens
    # If text contains only tokens and no actual PII patterns, it's safe
    actual_leaks = {}
    for leak_type, count in leaks.items():
        # Only count as leak if it's not part of a token
        # This is a conservative check - if we see the pattern but it might be in a token, skip
        if count > 0:
            # For now, we count all matches as potential leaks
            # But we could improve this by checking context
            actual_leaks[leak_type] = count
    
    # Count total leaks (excluding false positives from tokens)
    total_leaks = sum(actual_leaks.values())
    
    if total_leaks > 0:
        leak_details = {k: v for k, v in actual_leaks.items() if v > 0}
        raise PrivacyLeakError(
            f"Privacy leak detected: {total_leaks} potential PII entities remaining",
            error_code="privacy_leak_detected"
        )

