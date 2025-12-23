"""
FastAPI main application entry point.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.models import (
    IngestRequest, IngestResponse,
    ScrubRequest, ScrubResponse,
    DraftRequest, DraftResponse
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
        event = await create_event(request.input_type, request.value)
        
        # Store in memory (session-based, never persisted)
        store_event(event)
        
        return IngestResponse(event_id=event.event_id, status="created")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error ingesting data: {str(e)}")


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


@app.post("/api/v1/draft/generate", response_model=DraftResponse)
async def generate_draft(request: DraftRequest):
    """
    Generate source-bound draft.
    
    CRITICAL: External API calls require is_anonymized=true ALWAYS,
    regardless of Production Mode.
    """
    from app.modules.drafting.excerpt_extractor import extract_excerpts
    from app.modules.drafting.llm_service import llm_service
    from app.modules.drafting.citation_mapper import map_citations
    from app.modules.drafting.validator import validate_draft
    from app.modules.privacy.privacy_service import get_event
    
    # CRITICAL: Verify that clean_text is actually anonymized
    # Check if text contains anonymization tokens or if it's the original
    # In production, we'd store scrubbed payloads and verify from store
    has_anonymization_tokens = any(
        token in request.clean_text 
        for token in ["[PERSON", "[ORG", "[EMAIL", "[PHONE", "[ADDRESS"]
    )
    
    # If no tokens and text looks like it might contain PII, it's not anonymized
    # Simple heuristic: if text contains email patterns or phone patterns, it's likely not anonymized
    import re
    has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', request.clean_text))
    has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', request.clean_text))
    
    is_anonymized = has_anonymization_tokens or (not has_email and not has_phone)
    
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

