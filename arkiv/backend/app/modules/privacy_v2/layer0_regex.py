"""
Layer 0: Deterministic regex-based pre-flight sanitization.

No AI, pure regex. Metrics only, never log text.
"""
import re
from typing import Dict, Tuple


def sanitize_preflight(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Pre-flight sanitization with regex patterns.
    
    Args:
        text: Raw text to sanitize
        
    Returns:
        (sanitized_text, metrics) where metrics contains counts only
    """
    metrics = {
        "emails_found": 0,
        "phones_found": 0,
        "ssns_found": 0,
        "ibans_found": 0
    }
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    metrics["emails_found"] = len(emails)
    for email in emails:
        text = text.replace(email, "[EMAIL_PREFLIGHT]")
    
    # Phone patterns
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        r'\b0\d{1,2}[-.\s]?\d{3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b',  # Swedish
    ]
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))
    metrics["phones_found"] = len(set(phones))
    for phone in set(phones):
        text = text.replace(phone, "[PHONE_PREFLIGHT]")
    
    # SSN pattern
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    ssns = re.findall(ssn_pattern, text)
    metrics["ssns_found"] = len(ssns)
    for ssn in ssns:
        text = text.replace(ssn, "[SSN_PREFLIGHT]")
    
    # IBAN-like patterns (basic)
    iban_pattern = r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,}\d{7,}\b'
    ibans = re.findall(iban_pattern, text)
    metrics["ibans_found"] = len(ibans)
    for iban in ibans:
        text = text.replace(iban, "[IBAN_PREFLIGHT]")
    
    return text, metrics

