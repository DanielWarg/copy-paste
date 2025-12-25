"""SQLAlchemy models for projects module."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    """Project model - backbone for all artifacts."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    sensitivity = Column(String, nullable=False, default="standard", index=True)  # standard|sensitive
    status = Column(String, nullable=False, default="active", index=True)  # active|archived|destroyed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_working_at = Column(DateTime, nullable=True, index=True)  # Set on first artifact attachment
    start_date = Column(Date, nullable=False, server_default=func.current_date(), index=True)  # Project start date
    due_date = Column(Date, nullable=True, index=True)  # Project deadline (optional)

    # Relationships
    notes = relationship("ProjectNote", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    audit_events = relationship("ProjectAuditEvent", back_populates="project", cascade="all, delete-orphan")


class ProjectNote(Base):
    """Project note - user-created text notes."""

    __tablename__ = "project_notes"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    body_text = Column(Text, nullable=False)  # Content stored here
    note_integrity_hash = Column(String, nullable=False, index=True)  # SHA256 of body_text
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="notes")


class ProjectFile(Base):
    """Project file - uploaded files with encryption."""

    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)  # Only in DB, never on disk
    sha256 = Column(String, nullable=False, unique=True, index=True)  # Content hash
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    stored_encrypted = Column(Boolean, nullable=False, default=True)
    storage_path = Column(String, nullable=False)  # Internal path: {sha256}.bin
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    project = relationship("Project", back_populates="files")


class ProjectAuditEvent(Base):
    """Global project audit event - NO CONTENT, only metadata."""

    __tablename__ = "project_audit_events"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # created|updated|note_created|file_uploaded|integrity_checked|flagged|destroyed
    severity = Column(String, nullable=False, default="info", index=True)  # info|warning|critical
    actor = Column(String, nullable=True, default="system")
    request_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metadata_json = Column(JSON, nullable=True)  # STRICT: counts, ids, format - NEVER content

    # Relationships
    project = relationship("Project", back_populates="audit_events")

    # Index for common queries
    __table_args__ = (
        Index("idx_audit_project_severity", "project_id", "severity"),
    )

