"""
Adapters for different input types (URL, text, PDF).

MCP-style data entry - normalizes all inputs to standardized format.
"""
import httpx
import re
from typing import Optional
from PyPDF2 import PdfReader
from io import BytesIO


async def fetch_url_content(url: str) -> str:
    """
    Fetch content from URL.
    
    Args:
        url: URL to fetch
        
    Returns:
        Extracted text content
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # Basic HTML text extraction (simple, no external deps)
            text = response.text
            
            # Remove script and style tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text[:10000]  # Limit to 10k chars for demo
            
    except Exception as e:
        return f"[Error fetching URL: {str(e)}]"


def extract_pdf_content(pdf_data: bytes) -> str:
    """
    Extract text from PDF.
    
    Args:
        pdf_data: PDF file bytes
        
    Returns:
        Extracted text content
    """
    try:
        pdf_file = BytesIO(pdf_data)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        for page in reader.pages[:10]:  # Limit to first 10 pages for demo
            text_parts.append(page.extract_text())
        
        text = '\n\n'.join(text_parts)
        return text[:10000]  # Limit to 10k chars for demo
        
    except Exception as e:
        return f"[Error extracting PDF: {str(e)}]"


def normalize_text(text: str) -> str:
    """
    Normalize raw text input.
    
    Args:
        text: Raw text input
        
    Returns:
        Normalized text
    """
    # Basic normalization
    text = re.sub(r'\s+', ' ', text)
    return text.strip()[:10000]  # Limit to 10k chars for demo

