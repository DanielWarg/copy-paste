"""
Brief generation endpoint - RAG-powered content generation
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from ..core.database import get_db
from ..core.middleware import APIKeyAuth, check_concurrency, increment_concurrency, decrement_concurrency
from ..services.audit_service import AuditService
from ..services.rag_service import RAGService
from ..services.output_sanitizer import sanitize_json_output

router = APIRouter(prefix="/api/v1", tags=["brief"])
api_key_auth = APIKeyAuth()


class BriefRequest(BaseModel):
    """Request model for brief generation"""
    source_ids: List[str] = Field(..., description="List of source IDs to use")
    query: Optional[str] = Field(None, description="Optional query to focus the brief")


class Citation(BaseModel):
    """Citation model"""
    chunk_id: str
    text: str
    source_id: str
    source_url: str


class BriefResponse(BaseModel):
    """Response model for brief generation"""
    brief: str
    factbox: List[dict]
    draft: str
    open_questions: List[str]
    citations: List[Citation]
    risk_flags: List[str]


@router.post("/brief", response_model=BriefResponse)
async def generate_brief(
    request: BriefRequest,
    req: Request,
    api_key: str = Depends(api_key_auth),
    db: Session = Depends(get_db),
):
    """
    Generate a brief using RAG
    
    - Retrieves relevant chunks from sources
    - Generates brief, factbox, draft, and open questions
    - Returns citations for all claims
    - Logs to audit trail
    """
    trace_id = req.state.trace_id
    
    # Check concurrency limit
    check_concurrency(api_key)
    increment_concurrency(api_key)
    
    try:
        # Generate brief using RAG
        rag_service = RAGService()
        brief_schema, citations = await rag_service.generate_brief(
            db=db,
            source_ids=request.source_ids,
            query=request.query,
        )
        
        # Sanitize output
        sanitized_factbox = sanitize_json_output(brief_schema.factbox)
        sanitized_citations = sanitize_json_output(citations)
        
        # Log to audit trail
        AuditService.log_operation(
            db=db,
            user_id=api_key,
            operation="brief",
            source_ids=request.source_ids,
            trace_id=trace_id,
            metadata={"query": request.query},
            output=brief_schema.brief,
        )
        
        return BriefResponse(
            brief=brief_schema.brief,
            factbox=sanitized_factbox,
            draft=brief_schema.draft,
            open_questions=brief_schema.open_questions,
            citations=sanitized_citations,
            risk_flags=brief_schema.risk_flags,
        )
        
    except ValueError as e:
        # Schema validation failed - return safe fallback
        # Still log to audit trail
        AuditService.log_operation(
            db=db,
            user_id=api_key,
            operation="brief",
            source_ids=request.source_ids,
            trace_id=trace_id,
            metadata={"query": request.query, "error": str(e)},
        )
        
        # Return safe fallback with citations if available
        return BriefResponse(
            brief="Kunde inte generera strukturerat svar. Se källor nedan.",
            factbox=[],
            draft="",
            open_questions=[],
            citations=[],
            risk_flags=["Schema validation failed"],
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate brief: {str(e)}")
    finally:
        decrement_concurrency(api_key)

