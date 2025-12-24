"""
Event Creator - Normalizes inputs to StandardizedEvent.

MCP-style data entry: all inputs become standardized events.
"""
from uuid import uuid4, UUID
from app.models import StandardizedEvent
from app.modules.ingestion.adapters import fetch_url_content, extract_pdf_content, normalize_text
from typing import Literal, Optional, Dict, Any
import base64


async def create_event(
    input_type: Literal["url", "text", "pdf"],
    value: str,
    metadata: Optional[Dict[str, Any]] = None
) -> StandardizedEvent:
    """
    Create standardized event from input.
    
    Args:
        input_type: Type of input (url, text, pdf)
        value: Input value (URL, text content, or base64-encoded PDF)
        
    Returns:
        StandardizedEvent object
    """
    event_id = uuid4()
    
    # Start with provided metadata or empty dict
    event_metadata = dict(metadata) if metadata else {}
    
    if input_type == "url":
        raw_payload = await fetch_url_content(value)
        source_type = "web"
        event_metadata.update({"url": value, "input_type": "url"})
        
        # If scout_source is present, set source_type to "rss"
        if "scout_source" in event_metadata:
            source_type = "rss"
        
    elif input_type == "text":
        raw_payload = normalize_text(value)
        source_type = "manual"
        event_metadata.update({"input_type": "text", "length": len(raw_payload)})
        
        # If scout_source is present, set source_type to "rss"
        if "scout_source" in event_metadata:
            source_type = "rss"
        
    elif input_type == "pdf":
        # Decode base64 PDF
        try:
            pdf_data = base64.b64decode(value)
            raw_payload = extract_pdf_content(pdf_data)
            source_type = "manual"
            event_metadata.update({"input_type": "pdf", "length": len(raw_payload)})
        except Exception as e:
            raw_payload = f"[Error processing PDF: {str(e)}]"
            source_type = "manual"
            event_metadata.update({"input_type": "pdf", "error": str(e)})
    else:
        raise ValueError(f"Invalid input_type: {input_type}")
    
    return StandardizedEvent(
        event_id=event_id,
        source_type=source_type,
        raw_payload=raw_payload,
        metadata=event_metadata
    )

