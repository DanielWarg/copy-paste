"""
MCP Adapter - Thin wrapper for MCP-compatible ingestion.

This adapter demonstrates MCP thinking (stable contracts, adapters, tool-oriented interface)
without modifying core ingestion logic. It reuses the exact same functions as /api/v1/ingest.
"""
from app.models import MCPIngestRequest, MCPToolResponse
from app.modules.ingestion.event_creator import create_event
from app.modules.privacy.privacy_service import store_event


async def mcp_ingest(request: MCPIngestRequest) -> MCPToolResponse:
    """
    MCP-compatible ingestion adapter.
    
    This is a thin wrapper that:
    - Validates tool is 'ingest' (v1 limitation)
    - Calls the exact same create_event() used by /api/v1/ingest
    - Calls the exact same store_event() used by /api/v1/ingest
    - Returns MCP-style response with explicit ok/error structure
    
    Args:
        request: MCPIngestRequest with tool, input_type, value, metadata
        
    Returns:
        MCPToolResponse with ok, event_id (on success), or error (on failure)
    """
    # Explicit v1 guard: only 'ingest' tool is supported
    if request.tool != "ingest":
        return MCPToolResponse(
            ok=False,
            error="Only 'ingest' tool is supported in MCP v1"
        )
    
    try:
        # Reuse exact same logic as /api/v1/ingest endpoint
        event = await create_event(
            request.input_type,
            request.value,
            request.metadata
        )
        
        # Store event using exact same function
        store_event(event)
        
        return MCPToolResponse(
            ok=True,
            event_id=event.event_id,
            error=None
        )
    except ValueError as e:
        # Validation errors (e.g., invalid input_type)
        return MCPToolResponse(
            ok=False,
            error=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Other errors (e.g., network errors, parsing errors)
        return MCPToolResponse(
            ok=False,
            error=f"Error ingesting data: {str(e)}"
        )

