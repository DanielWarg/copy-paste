"""
Data Contracts (Pydantic Models) - THE TRUTH

All data structures that flow through the system.
GDPR-compliant: raw_payload in-memory only, mapping ephemeral only.
"""
from typing import Dict, List, Literal, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class StandardizedEvent(BaseModel):
    """
    Standardized Event Object - Single source of truth for all ingested data.
    
    GDPR: raw_payload is IN-MEMORY ONLY - never persisted, session-based.
    """
    event_id: UUID
    source_type: Literal["rss", "web", "manual"]
    raw_payload: str = Field(
        ...,
        description="IN-MEMORY ONLY - never persisted, session-based. Contains raw input from URL/text/PDF."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="URL, timestamp, and other non-sensitive metadata"
    )


class ScrubbedPayload(BaseModel):
    """
    Scrubbed Payload - Production-safe text after anonymization.
    
    GDPR: mapping is EPHEMERAL ONLY - never persisted, never in response, only in server RAM.
    """
    event_id: UUID
    clean_text: str = Field(
        ...,
        description="Anonymized text containing [PERSON_A], [ORG_B] etc. tokens"
    )
    is_anonymized: bool = Field(
        ...,
        description="Must be True for external API calls. Always required, regardless of Production Mode."
    )
    # mapping: Dict[str, str]  # EPHEMERAL ONLY - never persisted, never in response, only in server RAM with TTL


class Citation(BaseModel):
    """Citation mapping for source-bound claims."""
    id: str = Field(..., description="Source identifier (e.g., 'source_1')")
    excerpt: str = Field(..., description="Original source fragment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class DraftObject(BaseModel):
    """
    Source-Bound Draft - AI-generated text with enforced traceability.
    
    Every claim must reference at least one source_id.
    Claims without sources are flagged in policy_violations.
    """
    text: str = Field(
        ...,
        description="Generated text with [source_1] markers for citations"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of all citations referenced in the text"
    )
    policy_violations: List[str] = Field(
        default_factory=list,
        description="List of policy violations, e.g., ['uncited_claims']"
    )


# Request/Response models for API endpoints

class IngestRequest(BaseModel):
    """Request model for /api/v1/ingest"""
    input_type: Literal["url", "text", "pdf"]
    value: str = Field(..., description="URL, raw text, or PDF content")


class IngestResponse(BaseModel):
    """Response model for /api/v1/ingest"""
    event_id: UUID
    status: str = "created"


class ScrubRequest(BaseModel):
    """Request model for /api/v1/privacy/scrub"""
    event_id: UUID
    production_mode: bool = Field(
        ...,
        description="Production Mode flag sent in request (no global backend state)"
    )


class ScrubResponse(BaseModel):
    """Response model for /api/v1/privacy/scrub"""
    event_id: UUID
    clean_text: str
    is_anonymized: bool
    # mapping is NEVER included in response


class DraftRequest(BaseModel):
    """Request model for /api/v1/draft/generate"""
    event_id: UUID
    clean_text: str
    production_mode: bool = Field(
        ...,
        description="Production Mode flag sent in request (no global backend state)"
    )


class DraftResponse(BaseModel):
    """Response model for /api/v1/draft/generate"""
    text: str
    citations: List[Citation]
    policy_violations: List[str]

