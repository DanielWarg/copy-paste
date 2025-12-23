"""
Layer 2: Deterministic post-check verification.

Re-runs regex checks on clean_text. If PII remains, triggers retry.
"""
import re
from typing import Tuple, List


def verify_anonymization(clean_text: str) -> Tuple[bool, List[str]]:
    """
    Verify that clean_text contains no obvious PII.
    
    Args:
        clean_text: Anonymized text to verify
        
    Returns:
        (passed, failures) where failures is list of detected patterns
    """
    failures = []
    
    # Check for email patterns
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', clean_text):
        failures.append("email_pattern_detected")
    
    # Check for phone patterns (American + Swedish + International)
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # American format
        r'\b0\d{1,2}[-.\s]?\d{3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b',  # Swedish format (08-123 45 67, 070-1234567)
        r'\b\+46\s?\d{1,2}[-.\s]?\d{3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b',  # International Swedish (+46 8 123 45 67)
    ]
    for pattern in phone_patterns:
        if re.search(pattern, clean_text):
            failures.append("phone_pattern_detected")
            break  # Only add once
    
    # Check for SSN patterns
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', clean_text):
        failures.append("ssn_pattern_detected")
    
    # Check for obvious names (capitalized words)
    # This is a heuristic - might have false positives
    name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
    if len(re.findall(name_pattern, clean_text)) > 3:  # Threshold
        failures.append("potential_name_patterns")
    
    return len(failures) == 0, failures

