"""
Chunking service - split text into chunks with deduplication
"""
from typing import List
from ..core.security import compute_hash
import re


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[dict]:
    """
    Split text into chunks with overlap
    
    Returns:
        List of chunks with text and hash
    """
    # Clean text
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) <= chunk_size:
        # Single chunk
        text_hash = compute_hash(text)
        return [{
            "text": text,
            "text_hash": text_hash,
            "chunk_index": 0,
        }]
    
    # Split into chunks
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending
            sentence_end = max(
                text.rfind('.', start, end),
                text.rfind('!', start, end),
                text.rfind('?', start, end),
            )
            if sentence_end > start:
                end = sentence_end + 1
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            text_hash = compute_hash(chunk_text)
            chunks.append({
                "text": chunk_text,
                "text_hash": text_hash,
                "chunk_index": chunk_index,
            })
            chunk_index += 1
        
        # Move start with overlap
        start = end - chunk_overlap
    
    return chunks


def dedupe_chunks(chunks: List[dict], existing_hashes: set[str]) -> List[dict]:
    """
    Remove duplicate chunks based on text hash
    
    Args:
        chunks: List of chunk dicts with text_hash
        existing_hashes: Set of existing text hashes
    
    Returns:
        Filtered list of unique chunks
    """
    unique_chunks = []
    seen_hashes = set(existing_hashes)
    
    for chunk in chunks:
        chunk_hash = chunk["text_hash"]
        if chunk_hash not in seen_hashes:
            unique_chunks.append(chunk)
            seen_hashes.add(chunk_hash)
    
    return unique_chunks

