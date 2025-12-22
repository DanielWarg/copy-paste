"""
Index endpoint - trigger indexing of sources
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from ..core.database import get_db
from ..core.middleware import APIKeyAuth
from ..services.audit_service import AuditService
from ..services.chunking import chunk_text, dedupe_chunks
from ..services.embeddings import get_embedding_provider
from ..models.source import Source
from ..models.chunk import Chunk
from sqlalchemy import func

router = APIRouter(prefix="/api/v1", tags=["index"])
api_key_auth = APIKeyAuth()


class IndexRequest(BaseModel):
    """Request model for index endpoint"""
    source_ids: Optional[List[str]] = Field(None, description="Source IDs to index (all if empty)")


class IndexResponse(BaseModel):
    """Response model for index endpoint"""
    status: str
    message: str
    indexed_count: int


@router.post("/index", response_model=IndexResponse)
async def index_sources(
    request: IndexRequest,
    req: Request,
    api_key: str = Depends(api_key_auth),
    db: Session = Depends(get_db),
):
    """
    Index sources (create embeddings and chunks)
    
    - Processes sources into chunks
    - Generates embeddings
    - Stores in vector database
    - Logs to audit trail
    """
    trace_id = req.state.trace_id
    
    try:
        # Get sources to index
        if request.source_ids:
            sources = db.query(Source).filter(Source.id.in_(request.source_ids)).all()
        else:
            sources = db.query(Source).all()
        
        if not sources:
            return IndexResponse(
                status="success",
                message="No sources to index",
                indexed_count=0,
            )
        
        # Get embedding provider
        embedding_provider = get_embedding_provider()
        
        # Get existing chunk hashes for dedupe
        existing_hashes = set(
            db.query(Chunk.text_hash).filter(
                Chunk.source_id.in_([str(s.id) for s in sources])
            ).all()
        )
        existing_hashes = {h[0] for h in existing_hashes}
        
        indexed_count = 0
        
        for source in sources:
            if not source.raw_content:
                continue
            
            # Chunk the content
            chunks = chunk_text(source.raw_content)
            
            # Dedupe
            unique_chunks = dedupe_chunks(chunks, existing_hashes)
            
            if not unique_chunks:
                continue
            
            # Generate embeddings
            texts = [chunk["text"] for chunk in unique_chunks]
            embeddings = await embedding_provider.embed_batch(texts)
            
            # Create chunk records
            for chunk_data, embedding in zip(unique_chunks, embeddings):
                chunk = Chunk(
                    source_id=source.id,
                    chunk_index=chunk_data["chunk_index"],
                    text=chunk_data["text"],
                    text_hash=chunk_data["text_hash"],
                    embedding=embedding,
                    token_count=len(chunk_data["text"].split()),
                )
                db.add(chunk)
                existing_hashes.add(chunk_data["text_hash"])
            
            indexed_count += len(unique_chunks)
        
        db.commit()
        
        # Log to audit trail
        AuditService.log_operation(
            db=db,
            user_id=api_key,
            operation="index",
            source_ids=[str(s.id) for s in sources],
            trace_id=trace_id,
            metadata={"indexed_count": indexed_count},
        )
        
        return IndexResponse(
            status="success",
            message=f"Indexed {indexed_count} chunks from {len(sources)} sources",
            indexed_count=indexed_count,
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to index: {str(e)}")

