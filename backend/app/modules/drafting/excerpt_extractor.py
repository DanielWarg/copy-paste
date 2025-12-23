"""
Excerpt Extractor - Extract relevant excerpts from sources.

Replaces "RAG processing" with simple excerpt extraction.
"""
from typing import List, Dict
from app.models import Citation


def extract_excerpts(text: str, max_excerpts: int = 5) -> List[Citation]:
    """
    Extract relevant excerpts from text.
    
    Simple implementation: splits text into sentences and returns first N.
    In production, this could use more sophisticated extraction.
    
    Args:
        text: Source text
        max_excerpts: Maximum number of excerpts to return
        
    Returns:
        List of Citation objects
    """
    import re
    
    # Split into sentences
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]  # Min 20 chars
    
    # Take first N sentences as excerpts
    excerpts = sentences[:max_excerpts]
    
    citations = []
    for i, excerpt in enumerate(excerpts, 1):
        citations.append(Citation(
            id=f"source_{i}",
            excerpt=excerpt[:200],  # Limit excerpt length
            confidence=0.9 - (i * 0.1)  # Decreasing confidence
        ))
    
    return citations

