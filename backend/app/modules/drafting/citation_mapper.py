"""
Citation Mapper - Map claims to source citations.
"""
import re
from typing import List
from app.models import Citation


def map_citations(text: str, citations: List[Citation]) -> List[Citation]:
    """
    Map citation markers in text to actual citations.
    
    Args:
        text: Generated text with [source_X] markers
        citations: Available citations
        
    Returns:
        List of citations actually used in text
    """
    # Find all citation markers in text
    pattern = r'\[source_(\d+)\]'
    matches = re.findall(pattern, text)
    
    used_citation_ids = set(matches)
    
    # Map to actual citations
    used_citations = []
    for cit in citations:
        cit_num = cit.id.replace("source_", "")
        if cit_num in used_citation_ids:
            used_citations.append(cit)
    
    return used_citations

