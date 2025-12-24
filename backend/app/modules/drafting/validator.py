"""
Policy Validator - Detect policy violations in generated drafts.
"""
import re
from typing import List


def validate_draft(text: str) -> List[str]:
    """
    Validate draft for policy violations.
    
    Args:
        text: Generated draft text
        
    Returns:
        List of policy violations (empty if none)
    """
    violations = []
    
    # Check for uncited claims (sentences without citations)
    sentences = re.split(r'[.!?]+\s+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Only check substantial sentences
            # Check if sentence contains citation marker
            if not re.search(r'\[source_\d+\]', sentence):
                # This is a potential uncited claim
                violations.append("uncited_claims")
                break  # Only flag once
    
    return list(set(violations))  # Remove duplicates

