"""
Sources endpoints - list and query sources
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..core.middleware import APIKeyAuth
from ..models.source import Source
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["sources"])
api_key_auth = APIKeyAuth()


class SourceResponse(BaseModel):
    """Source response model"""
    id: str
    url: str
    source_type: str
    title: Optional[str]
    source_hash: str
    content_version: int
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/sources", response_model=List[SourceResponse])
async def list_sources(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    api_key: str = Depends(api_key_auth),
    db: Session = Depends(get_db),
):
    """List all sources"""
    sources = db.query(Source).offset(offset).limit(limit).all()
    return [
        SourceResponse(
            id=str(s.id),
            url=s.url,
            source_type=s.source_type,
            title=s.title,
            source_hash=s.source_hash,
            content_version=s.content_version,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in sources
    ]

