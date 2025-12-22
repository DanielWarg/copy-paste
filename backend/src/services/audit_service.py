"""
Audit trail service - logs all operations
"""
from sqlalchemy.orm import Session
from ..models.audit import AuditLog
from ..core.security import compute_hash
from typing import Optional, List, Dict, Any
import uuid


class AuditService:
    """Service for logging audit trails"""
    
    @staticmethod
    def log_operation(
        db: Session,
        user_id: str,
        operation: str,
        source_ids: Optional[List[str]] = None,
        source_hash: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
        retrieved_chunks: Optional[List[str]] = None,
        output: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log an operation to audit trail"""
        output_hash = None
        output_preview = None
        
        if output:
            output_hash = compute_hash(output)
            output_preview = output[:1000]  # First 1000 chars
        
        audit_log = AuditLog(
            user_id=user_id,
            operation=operation,
            source_ids=source_ids,
            source_hash=source_hash,
            model_name=model_name,
            prompt_version=prompt_version,
            retrieved_chunks=retrieved_chunks,
            output_hash=output_hash,
            output_preview=output_preview,
            trace_id=trace_id or str(uuid.uuid4()),
            metadata=metadata,
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log

