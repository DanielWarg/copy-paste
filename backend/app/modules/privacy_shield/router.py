"""Privacy Shield Router - API endpoints for PII masking."""
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request

from app.core.logging import logger
from app.modules.privacy_shield.models import (
    PrivacyMaskRequest,
    PrivacyMaskResponse,
    PrivacyLeakError
)
from app.modules.privacy_shield.service import mask_text

router = APIRouter()


@router.post("/mask", response_model=PrivacyMaskResponse)
async def mask(request_body: PrivacyMaskRequest, http_request: Request) -> PrivacyMaskResponse:
    """
    Mask PII in text using defense-in-depth pipeline.
    
    Pipeline:
    1. Baseline regex mask (always runs)
    2. Leak check (blocking)
    3. Control check (advisory, strict mode only)
    
    Returns:
        PrivacyMaskResponse with masked text and metadata
        
    Raises:
        HTTPException: 413 if input too large, 422 if leak detected, 500 on error
    """
    # Get request ID from middleware (set by RequestIDMiddleware)
    request_id = getattr(http_request.state, "request_id", None) or str(uuid4())
    
    logger.info(
        "privacy_mask_request",
        extra={
            "request_id": request_id,
            "mode": request_body.mode,
            "language": request_body.language,
            "text_length": len(request_body.text)
        }
    )
    
    try:
        response = await mask_text(request_body, request_id)
        return response
    except HTTPException:
        raise
    except PrivacyLeakError as e:
        logger.error(
            "privacy_mask_leak_detected",
            extra={
                "request_id": request_id,
                "error_type": type(e).__name__,
                "error_code": e.error_code
            }
        )
        raise HTTPException(
            status_code=422,
            detail="Privacy leak detected"
        )
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "privacy_mask_failed",
            extra={
                "request_id": request_id,
                "error_type": error_type
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Privacy masking failed"
        )

