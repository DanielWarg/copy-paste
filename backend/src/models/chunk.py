"""
Chunk model - represents text chunks from sources with embeddings
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Index, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Chunk(Base):
    """Text chunk with embedding vector"""
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # Order within source
    text = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for dedupe
    embedding = Column(ARRAY(Float))  # pgvector will use this - Float imported below
    token_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    source = relationship("Source", backref="chunks")
    
    __table_args__ = (
        Index("idx_chunk_text_hash", "text_hash"),  # For dedupe
        Index("idx_chunk_source", "source_id", "chunk_index"),
    )

