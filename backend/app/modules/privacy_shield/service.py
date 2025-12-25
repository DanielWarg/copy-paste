"""Privacy Shield Service - Defense-in-depth pipeline + policy."""
import time
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import logger
from app.modules.privacy_shield.models import (
    PrivacyMaskRequest,
    PrivacyMaskResponse,
    PrivacyLog,
    ControlResult,
    MaskedPayload,
    PrivacyLeakError
)
from app.modules.privacy_shield.regex_mask import regex_masker
from app.modules.privacy_shield.leak_check import check_leaks
from app.modules.privacy_shield.providers.llamacpp_provider import llamacpp_provider


async def mask_text(request: PrivacyMaskRequest, request_id: str) -> PrivacyMaskResponse:
    """
    Mask text using defense-in-depth pipeline.
    
    Pipeline:
    1. Baseline regex mask (MUST always run)
    2. Leak check (blocking)
    3. Control check (advisory, strict mode only)
    4. Return response
    
    Args:
        request: Mask request
        request_id: Request ID for tracking
        
    Returns:
        PrivacyMaskResponse
        
    Raises:
        HTTPException: If validation fails or leak detected
    """
    start_time = time.time()
    
    # Validate input length
    if len(request.text) > settings.privacy_max_chars:
        logger.error(
            "privacy_mask_input_too_large",
            extra={
                "request_id": request_id,
                "length": len(request.text),
                "max_chars": settings.privacy_max_chars,
                "error_type": "ValidationError"
            }
        )
        raise HTTPException(
            status_code=413,
            detail=f"Input text exceeds maximum length ({settings.privacy_max_chars} characters)"
        )
    
    # A) Baseline mask (MUST always run) - Multi-pass for robustness
    try:
        # Pass 1: Initial masking
        masked_text, entity_counts, privacy_logs = regex_masker.mask(request.text)
        provider = "regex"
        
        # Pass 2: Re-mask on result (catches overlaps, edge cases, missed hits)
        # This is critical for edge cases with many repetitions
        masked_text_pass2, additional_counts, additional_logs = regex_masker.mask(masked_text)
        
        # Only use pass2 if it actually changed something (avoid infinite loops)
        if masked_text_pass2 != masked_text:
            masked_text = masked_text_pass2
            # Merge counts and logs
            for key in entity_counts:
                entity_counts[key] += additional_counts.get(key, 0)
            privacy_logs.extend(additional_logs)
        
        # Pass 3 (strict mode only): One more pass for maximum safety
        if request.mode == "strict":
            masked_text_pass3, additional_counts3, additional_logs3 = regex_masker.mask(masked_text)
            if masked_text_pass3 != masked_text:
                masked_text = masked_text_pass3
                for key in entity_counts:
                    entity_counts[key] += additional_counts3.get(key, 0)
                privacy_logs.extend(additional_logs3)
                
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "privacy_mask_baseline_failed",
            extra={
                "request_id": request_id,
                "error_type": error_type
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Baseline masking failed"
        )
    
    # B) Leak check (BLOCKING) - Must pass after multi-pass masking
    try:
        check_leaks(masked_text, mode=request.mode)
    except PrivacyLeakError as e:
        # After multi-pass masking, any leak is a hard failure
        logger.error(
            "privacy_mask_leak_detected",
            extra={
                "request_id": request_id,
                "error_type": "PrivacyLeakError",
                "error_code": e.error_code
            }
        )
        from app.core.errors import create_error_response
        from fastapi import Request
        # Create error response with standard error shape
        # Note: We can't access request here, so we use a generic one
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "pii_detected",
                    "message": "Privacy leak detected after masking",
                    "request_id": request_id
                }
            }
        )
    
    # C) Control check (ADVISORY, strict mode only)
    control_result = ControlResult(ok=True, reasons=[])
    if request.mode == "strict" and llamacpp_provider.is_enabled():
        try:
            # Create MaskedPayload for control check
            masked_payload = MaskedPayload(
                text=masked_text,
                entities=entity_counts,
                privacy_logs=privacy_logs,
                request_id=request_id
            )
            control_result_dict = await llamacpp_provider.control_check(masked_payload)
            control_result = ControlResult(
                ok=control_result_dict.get("ok", True),
                reasons=control_result_dict.get("reasons", [])
            )
            
            # If control check says NOT OK, apply conservative extra masking
            if not control_result.ok:
                masked_text, additional_counts, additional_logs = regex_masker.mask(masked_text)
                for key in entity_counts:
                    entity_counts[key] += additional_counts.get(key, 0)
                privacy_logs.extend(additional_logs)
                
                # Check again
                try:
                    check_leaks(masked_text, mode="strict")
                except PrivacyLeakError as e:
                    logger.error(
                        "privacy_mask_control_check_failed",
                        extra={
                            "request_id": request_id,
                            "error_type": "PrivacyLeakError",
                            "error_code": e.error_code
                        }
                    )
                    raise HTTPException(
                        status_code=422,
                        detail="Privacy leak detected after control check"
                    )
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(
                "privacy_mask_control_check_error",
                extra={
                    "request_id": request_id,
                    "error_type": error_type
                }
            )
            # Control check failure is non-blocking (advisory)
    
    latency_ms = (time.time() - start_time) * 1000
    
    logger.info(
        "privacy_mask_complete",
        extra={
            "request_id": request_id,
            "mode": request.mode,
            "provider": provider,
            "latency_ms": round(latency_ms, 2)
        }
    )
    
    return PrivacyMaskResponse(
        maskedText=masked_text,
        summary=None,
        entities=entity_counts,
        privacyLogs=privacy_logs,
        provider=provider,
        requestId=request_id,
        control=control_result
    )

