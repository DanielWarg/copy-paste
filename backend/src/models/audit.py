"""
Audit trail model - logs all operations for traceability
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class AuditLog(Base):
    """Audit trail for all operations"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    user_id = Column(String(100))  # API key or user identifier
    operation = Column(String(50), nullable=False, index=True)  # ingest, index, brief, etc.
    source_ids = Column(JSONB)  # Array of source UUIDs involved
    source_hash = Column(String(64))  # Hash of input for dedupe detection
    model_name = Column(String(100))  # LLM model used
    prompt_version = Column(String(50))  # Version of prompt template
    retrieved_chunks = Column(JSONB)  # Array of chunk IDs retrieved
    output_hash = Column(String(64))  # Hash of output for verification
    output_preview = Column(Text)  # First 1000 chars of output
    trace_id = Column(String(64), index=True)  # For request tracing
    metadata = Column(JSONB)  # Additional metadata
    
    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user", "user_id", "timestamp"),
        Index("idx_audit_operation", "operation", "timestamp"),
        Index("idx_audit_trace", "trace_id"),
    )

