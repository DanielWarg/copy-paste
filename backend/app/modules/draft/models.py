"""Pydantic models for Draft API."""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class DraftRequest(BaseModel):
    """Request model for POST /api/v1/events/{event_id}/draft"""
    
    raw_text: str = Field(..., description="Raw text to generate draft from (will be masked via privacy_gate)")
    mode: Optional[Literal["strict", "balanced"]] = Field(default="strict", description="Privacy masking mode (default: strict)")


class DraftResponse(BaseModel):
    """Response model for draft creation"""
    
    draft_id: int = Field(..., description="Draft ID")
    event_id: int = Field(..., description="Event ID")
    content: str = Field(..., description="Generated draft content")
    created_at: str = Field(..., description="ISO timestamp")

