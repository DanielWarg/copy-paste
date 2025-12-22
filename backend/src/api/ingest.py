"""
Ingest endpoints - for ingesting URLs, PDFs, RSS feeds
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from ..core.database import get_db
from ..core.middleware import APIKeyAuth, check_concurrency, increment_concurrency, decrement_concurrency
from ..services.url_fetcher import URLFetcher, SSRFError
from ..services.audit_service import AuditService
from ..models.source import Source
from ..core.security import compute_hash
import uuid

router = APIRouter(prefix="/api/v1", tags=["ingest"])
api_key_auth = APIKeyAuth()


class IngestRequest(BaseModel):
    """Request model for ingest endpoint"""
    url: HttpUrl = Field(..., description="URL to ingest (HTTPS only)")
    source_type: str = Field(default="url", pattern="^(url|pdf|rss)$")


class IngestResponse(BaseModel):
    """Response model for ingest endpoint"""
    source_id: str
    status: str
    message: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_url(
    request: IngestRequest,
    req: Request,
    api_key: str = Depends(api_key_auth),
    db: Session = Depends(get_db),
):
    """
    Ingest a URL (HTTPS only, SSRF-protected)
    
    - Validates URL scheme (HTTPS only)
    - Blocks private IPs and metadata endpoints
    - Fetches content with size limits
    - Stores source with hash and version
    """
    trace_id = req.state.trace_id
    
    try:
        # Fetch URL content
        fetcher = URLFetcher()
        content_type, content_bytes = await fetcher.fetch(str(request.url))
        
        # Convert to string (assuming text content for now)
        content = content_bytes.decode('utf-8', errors='ignore')
        
        # Compute hash
        source_hash = compute_hash(content)
        
        # Check if source already exists
        existing_source = db.query(Source).filter(Source.url == str(request.url)).first()
        
        if existing_source:
            # Check if content changed
            if existing_source.source_hash != source_hash:
                # Content changed, increment version
                existing_source.content_version += 1
                existing_source.raw_content = content
                existing_source.source_hash = source_hash
                db.commit()
                db.refresh(existing_source)
            source_id = str(existing_source.id)
        else:
            # Create new source
            new_source = Source(
                url=str(request.url),
                source_type=request.source_type,
                raw_content=content,
                source_hash=source_hash,
            )
            db.add(new_source)
            db.commit()
            db.refresh(new_source)
            source_id = str(new_source.id)
        
        # Log to audit trail
        AuditService.log_operation(
            db=db,
            user_id=api_key,
            operation="ingest",
            source_ids=[source_id],
            source_hash=source_hash,
            trace_id=trace_id,
        )
        
        return IngestResponse(
            source_id=source_id,
            status="success",
            message=f"Source ingested successfully: {request.url}"
        )
        
    except SSRFError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest: {str(e)}")

