"""SQLAlchemy models for transcripts module."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Transcript(Base):
    """Transcript model - main transcript record."""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)  # "interview", "meeting", "upload"
    language = Column(String, nullable=False, default="sv", index=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(
        String,
        nullable=False,
        index=True,
        default="uploaded",
    )  # uploaded|transcribing|ready|reviewed|archived|deleted
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    raw_integrity_hash = Column(String, nullable=True, index=True)  # SHA256 of raw transcript content
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan")
    audit_events = relationship("TranscriptAuditEvent", back_populates="transcript", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    """Transcript segment model - individual text segments with timestamps."""

    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    start_ms = Column(Integer, nullable=False, index=True)
    end_ms = Column(Integer, nullable=False)
    speaker_label = Column(String, nullable=False, index=True)  # "SPEAKER_1", "SPEAKER_2", etc.
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # 0.0-1.0
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    transcript = relationship("Transcript", back_populates="segments")

    # Index for common queries
    __table_args__ = (
        Index("idx_segment_transcript_start", "transcript_id", "start_ms"),
    )


class TranscriptAuditEvent(Base):
    """Transcript audit event - NO CONTENT, only metadata."""

    __tablename__ = "transcript_audit_events"

    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # created|updated|segments_upserted|exported|deleted
    actor = Column(String, nullable=True, default="system")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)  # STRICT: NO transcript text, only counts/format/id

    # Relationships
    transcript = relationship("Transcript", back_populates="audit_events")

