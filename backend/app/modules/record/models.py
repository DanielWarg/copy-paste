"""Record module models - Audio assets."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class AudioAsset(Base):
    """Audio asset - encrypted audio file linked to transcript."""

    __tablename__ = "audio_assets"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    sha256 = Column(String, nullable=False, unique=True, index=True)  # Content hash
    mime_type = Column(String, nullable=False)  # audio/wav, audio/mpeg, etc.
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)  # Internal path: {sha256}.bin
    destroy_status = Column(String, nullable=False, default="none", index=True)  # none|pending|destroyed
    destroyed_at = Column(DateTime, nullable=True)  # Set when destroyed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    transcript = relationship("Transcript", foreign_keys=[transcript_id])

    # Index for common queries
    __table_args__ = (
        Index("idx_audio_transcript", "transcript_id"),
        Index("idx_audio_project", "project_id"),
    )

