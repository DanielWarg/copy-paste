"""
Event Creator - Normalizes inputs to StandardizedEvent.

MCP-style data entry: all inputs become standardized events.
"""
from uuid import uuid4, UUID
from app.models import StandardizedEvent
from app.modules.ingestion.adapters import fetch_url_content, extract_pdf_content, normalize_text
from typing import Literal
import base64


async def create_event(
    input_type: Literal["url", "text", "pdf"],
    value: str
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
    
    if input_type == "url":
        raw_payload = await fetch_url_content(value)
        source_type = "web"
        metadata = {"url": value, "input_type": "url"}
        
    elif input_type == "text":
        raw_payload = normalize_text(value)
        source_type = "manual"
        metadata = {"input_type": "text", "length": len(raw_payload)}
        
    elif input_type == "pdf":
        # Decode base64 PDF
        try:
            pdf_data = base64.b64decode(value)
            raw_payload = extract_pdf_content(pdf_data)
            source_type = "manual"
            metadata = {"input_type": "pdf", "length": len(raw_payload)}
        except Exception as e:
            raw_payload = f"[Error processing PDF: {str(e)}]"
            source_type = "manual"
            metadata = {"input_type": "pdf", "error": str(e)}
    else:
        raise ValueError(f"Invalid input_type: {input_type}")
    
    return StandardizedEvent(
        event_id=event_id,
        source_type=source_type,
        raw_payload=raw_payload,
        metadata=metadata
    )

