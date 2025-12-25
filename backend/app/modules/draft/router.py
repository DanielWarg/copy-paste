"""Draft Module Router - Event-based draft generation with Privacy Gate enforcement."""
from fastapi import APIRouter, HTTPException, Request, status

from app.core.logging import logger
from app.core.privacy_gate import ensure_masked_or_raise, PrivacyGateError
from app.modules.draft.models import DraftRequest, DraftResponse
from app.modules.draft.service import create_draft

router = APIRouter()


@router.post("/events/{event_id}/draft", status_code=status.HTTP_201_CREATED)
async def create_event_draft(
    event_id: int,
    request_body: DraftRequest,
    request: Request,
) -> DraftResponse:
    """
    Create draft for event with Privacy Gate enforcement.
    
    CRITICAL: All text MUST pass through privacy_gate before reaching any external LLM.
    
    Args:
        event_id: Event ID
        request_body: Draft request (raw_text, mode)
        request: FastAPI request (for request_id)
        
    Returns:
        DraftResponse with draft content
        
    Raises:
        HTTPException 422: If PII detected (privacy_gate blocks)
        HTTPException 404: If event not found
        HTTPException 500: If draft generation fails
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # STEP 1: Privacy Gate (OBLIGATORY - no bypass possible)
    try:
        masked_payload = await ensure_masked_or_raise(
            text=request_body.raw_text,
            mode=request_body.mode or "strict",
            request_id=request_id
        )
    except HTTPException as e:
        # Re-raise HTTPException (422 pii_detected, 413 too large, etc.)
        raise
    except PrivacyGateError as e:
        # Privacy gate failed - return 422
        logger.error(
            "draft_privacy_gate_failed",
            extra={
                "request_id": request_id,
                "event_id": event_id,
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "pii_detected",
                    "message": "PII detected in input - draft generation blocked",
                    "request_id": request_id
                }
            }
        )
    except Exception as e:
        # Unexpected error in privacy gate
        error_type = type(e).__name__
        logger.error(
            "draft_privacy_gate_error",
            extra={
                "request_id": request_id,
                "event_id": event_id,
                "error_type": error_type
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": "Privacy gate error",
                    "request_id": request_id
                }
            }
        )
    
    # STEP 2: Create draft using masked text only
    # masked_payload.text is guaranteed to have no direct PII
    try:
        draft = await create_draft(
            event_id=event_id,
            masked_text=masked_payload.text,
            request_id=request_id
        )
        return draft
    except ValueError as e:
        # Event not found, etc.
        logger.error(
            "draft_creation_failed",
            extra={
                "request_id": request_id,
                "event_id": event_id,
                "error_type": "ValueError"
            }
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "event_not_found",
                    "message": str(e),
                    "request_id": request_id
                }
            }
        )
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "draft_creation_error",
            extra={
                "request_id": request_id,
                "event_id": event_id,
                "error_type": error_type
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": "Draft generation failed",
                    "request_id": request_id
                }
            }
        )
