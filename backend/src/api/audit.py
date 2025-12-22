"""
Audit endpoints - query audit trail
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db
from ..core.middleware import APIKeyAuth
from ..models.audit import AuditLog
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["audit"])
api_key_auth = APIKeyAuth()


class AuditLogResponse(BaseModel):
    """Audit log response model"""
    id: str
    timestamp: str
    user_id: Optional[str]
    operation: str
    source_ids: Optional[List[str]]
    trace_id: Optional[str]
    output_preview: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/audit", response_model=List[AuditLogResponse])
async def query_audit(
    user_id: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    api_key: str = Depends(api_key_auth),
    db: Session = Depends(get_db),
):
    """Query audit trail"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if operation:
        query = query.filter(AuditLog.operation == operation)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    return [
        AuditLogResponse(
            id=str(log.id),
            timestamp=log.timestamp.isoformat() if log.timestamp else "",
            user_id=log.user_id,
            operation=log.operation,
            source_ids=log.source_ids,
            trace_id=log.trace_id,
            output_preview=log.output_preview,
        )
        for log in logs
    ]

