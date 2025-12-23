"""
FastAPI main application entry point.
"""
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.models import (
    IngestRequest, IngestResponse,
    ScrubRequest, ScrubResponse,
    DraftRequest, DraftResponse,
    MCPIngestRequest, MCPToolResponse,
    PrivacyScrubV2Request, PrivacyScrubV2Response,
    AudioIngestResponse
)
from app.modules.privacy.privacy_service import store_event, scrub_event
from uuid import uuid4

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Copy/Paste - Editorial AI Pipeline",
    description="Internal showreel system for editorial AI pipelines",
    version="1.0.0"
)

# Rate limiting middleware (must be first)
app.add_middleware(RateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.frontend_port}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Ingest source data (URL, text, or PDF).
    
    Creates a standardized event object.
    """
    from app.modules.ingestion.event_creator import create_event
    
    try:
        # Create standardized event
        event = await create_event(request.input_type, request.value, request.metadata)
        
        # Store in memory (session-based, never persisted)
        store_event(event)
        
        return IngestResponse(event_id=event.event_id, status="created")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error ingesting data: {str(e)}")


@app.post("/api/v1/mcp/ingest", response_model=MCPToolResponse)
async def mcp_ingest_endpoint(request: MCPIngestRequest):
    """
    MCP-compatible ingestion endpoint.
    
    Tool-oriented interface that wraps the existing ingestion logic.
    Returns MCP-style response with explicit ok/error structure.
    
    This endpoint uses the exact same internal functions as /api/v1/ingest,
    ensuring no duplication and consistent behavior.
    """
    from app.modules.ingestion.mcp_adapter import mcp_ingest
    return await mcp_ingest(request)


@app.post("/api/v1/ingest/audio", response_model=AudioIngestResponse)
async def ingest_audio(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    Ingest audio file - local transcription.
    
    Returns event_id. Transcript is stored in memory only.
    """
    from app.modules.ingestion.audio_ingest import ingest_audio as ingest_audio_service
    import json
    
    meta_dict = {}
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except:
            pass
    
    event_id = await ingest_audio_service(file, meta_dict)
    
    # CRITICAL: UploadFile.size doesn't exist - use len(content) or skip
    # We already read content in ingest_audio_service, so skip size here
    return AudioIngestResponse(
        event_id=event_id,
        status="created",
        transcript_meta={
            "filename": file.filename
        }
    )


@app.post("/api/v1/privacy/scrub", response_model=ScrubResponse)
async def scrub(request: ScrubRequest):
    """
    Scrub event payload - anonymize PII.
    
    Production Mode is sent in request (no global backend state).
    If Production Mode is ON and anonymization fails, returns HTTP 400.
    """
    result = await scrub_event(request.event_id, request.production_mode)
    
    return ScrubResponse(
        event_id=result.event_id,
        clean_text=result.clean_text,
        is_anonymized=result.is_anonymized
    )


@app.post("/api/v1/privacy/scrub_v2", response_model=PrivacyScrubV2Response)
async def scrub_v2(request: PrivacyScrubV2Request):
    """
    Privacy Shield v2: Multi-layer anonymization with verification loops.
    
    Returns approval_token if event is gated (verification_failed or semantic_risk).
    Production Mode = HARD STOP (no approval in production).
    """
    from app.modules.privacy_v2.privacy_v2_service import scrub_v2 as scrub_v2_service
    return await scrub_v2_service(request.event_id, request.production_mode, request.max_retries)


@app.post("/api/v1/draft/generate", response_model=DraftResponse)
async def generate_draft(request: DraftRequest):
    """
    Generate source-bound draft.
    
    CRITICAL: External API calls require:
    - is_anonymized=true ALWAYS
    - If approval_required=true (from scrub_v2), approval_token must be provided
    """
    from app.modules.drafting.excerpt_extractor import extract_excerpts
    from app.modules.drafting.llm_service import llm_service
    from app.modules.drafting.citation_mapper import map_citations
    from app.modules.drafting.validator import validate_draft
    from app.modules.privacy_v2.approval_manager import approval_manager
    from app.modules.privacy_v2.privacy_v2_status import privacy_v2_status_store
    
    # CRITICAL: Check privacy v2 status FIRST (read from RAM, don't guess from text)
    v2_status = privacy_v2_status_store.get_status(request.event_id)
    
    if v2_status and v2_status.gated:
        # Event is gated - MUST have valid approval_token
        if not request.approval_token:
            raise HTTPException(
                status_code=403,
                detail=f"Event is gated (verification_passed={v2_status.verification_passed}, semantic_risk={v2_status.semantic_risk}). approval_token required."
            )
        
        # Verify token matches event_id
        if not approval_manager.verify_token(request.approval_token, request.event_id):
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired approval_token"
            )
        
        # Verify token hash matches stored hash
        token_hash = approval_manager.get_token_hash(request.approval_token)
        if v2_status.approval_token_hash != token_hash:
            raise HTTPException(
                status_code=403,
                detail="approval_token hash mismatch"
            )
    
    # Legacy mode: If no v2_status exists, use existing heuristic (for backward compatibility)
    # This allows v1 scrub to still work
    if not v2_status:
        has_anonymization_tokens = any(
            token in request.clean_text 
            for token in ["[PERSON", "[ORG", "[EMAIL", "[PHONE", "[ADDRESS"]
        )
        
        import re
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', request.clean_text))
        has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', request.clean_text))
        
        is_anonymized = has_anonymization_tokens or (not has_email and not has_phone)
    else:
        # v2 mode: Use verification_passed and semantic_risk from status
        # CRITICAL: Don't assume True - scrub_v2 sets is_anonymized based on verification_passed and semantic_risk
        # If we got here with v2_status and gated=False, then gates passed
        is_anonymized = v2_status.verification_passed and not v2_status.semantic_risk
    
    # Extract relevant excerpts from scrubbed text
    citations = extract_excerpts(request.clean_text, max_excerpts=5)
    
    # Generate draft using LLM (with security check)
    # is_anonymized is verified above - LLM service will enforce it
    draft_text = await llm_service.generate_draft(
        clean_text=request.clean_text,
        is_anonymized=is_anonymized,  # Verified above
        event_id=str(request.event_id),
        citations=citations,
        production_mode=request.production_mode
    )
    
    # Map citations used in draft
    used_citations = map_citations(draft_text, citations)
    
    # Validate for policy violations
    violations = validate_draft(draft_text)
    
    return DraftResponse(
        text=draft_text,
        citations=used_citations,
        policy_violations=violations
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.backend_port)

