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
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata (e.g., scout_source, scout_feed_url, etc.)"
    )


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
    approval_token: Optional[str] = Field(
        None,
        description="Approval token required if event is gated (from scrub_v2)"
    )


class DraftResponse(BaseModel):
    """Response model for /api/v1/draft/generate"""
    text: str
    citations: List[Citation]
    policy_violations: List[str]


# MCP (Model Context Protocol) compatibility models

class MCPIngestRequest(BaseModel):
    """MCP-compatible ingestion request."""
    tool: Literal["ingest"] = Field(..., description="Tool identifier (only 'ingest' supported in v1)")
    input_type: Literal["url", "text", "pdf"] = Field(..., description="Type of input")
    value: str = Field(..., description="URL, raw text, or PDF content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (e.g., scout_source, scout_feed_url, etc.)"
    )
    correlation_id: Optional[str] = Field(
        None,
        description="Optional correlation ID for tracing"
    )


class MCPToolResponse(BaseModel):
    """MCP-compatible tool response."""
    ok: bool = Field(..., description="Success/failure indicator")
    event_id: Optional[UUID] = Field(None, description="Event ID on success")
    error: Optional[str] = Field(None, description="Error message on failure")


# Privacy Shield v2 models

class ReceiptStep(BaseModel):
    """Receipt step tracking for privacy processing."""
    name: str = Field(..., description="Step name (e.g., 'L0', 'L1', 'L2', 'L3', 'gate')")
    status: Literal["ok", "retry", "blocked", "failed"] = Field(..., description="Step status")
    model_id: Optional[str] = Field(None, description="Model identifier if applicable")
    started_at: str = Field(..., description="ISO timestamp when step started")
    ended_at: str = Field(..., description="ISO timestamp when step ended")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Step metrics (counts only)")


class Receipt(BaseModel):
    """Receipt tracking all privacy processing steps."""
    steps: List[ReceiptStep] = Field(default_factory=list, description="All processing steps")
    flags: List[str] = Field(default_factory=list, description="Flags (e.g., 'verification_failed', 'semantic_risk')")
    clean_text_sha256: str = Field(..., description="SHA256 hash of clean text")


class PrivacyScrubV2Request(BaseModel):
    """Request model for /api/v1/privacy/scrub_v2"""
    event_id: UUID
    production_mode: bool = Field(..., description="Production Mode flag sent in request")
    max_retries: int = Field(default=2, ge=0, le=3, description="Maximum retry attempts")


class PrivacyScrubV2Response(BaseModel):
    """Response model for /api/v1/privacy/scrub_v2"""
    event_id: UUID
    clean_text: str = Field(..., description="Anonymized text")
    is_anonymized: bool = Field(..., description="Always True if we got here")
    verification_passed: bool = Field(..., description="Whether verification passed")
    semantic_risk: bool = Field(..., description="Whether semantic risk detected")
    approval_required: bool = Field(..., description="Whether approval is required")
    approval_token: Optional[str] = Field(None, description="Approval token if gated")
    flags: List[str] = Field(default_factory=list, description="Processing flags")
    receipt: Receipt = Field(..., description="Processing receipt")


class AudioIngestResponse(BaseModel):
    """Response model for /api/v1/ingest/audio"""
    event_id: UUID
    status: str = Field(default="created", description="Ingestion status")
    transcript_meta: Dict[str, Any] = Field(default_factory=dict, description="Transcript metadata (no transcript text)")

