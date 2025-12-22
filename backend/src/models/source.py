"""
Source model - represents ingested content (URL, PDF, RSS)
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Source(Base):
    """Source of content (URL, PDF, RSS feed)"""
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # url, pdf, rss
    title = Column(String(500))
    raw_content = Column(Text)
    source_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash of raw_content
    content_version = Column(Integer, default=1, nullable=False)  # Increments when URL content changes
    metadata = Column(Text)  # JSON metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_source_hash", "source_hash"),
        Index("idx_source_url", "url"),
    )

