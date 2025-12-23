"""
Privacy Shield v2 Service - Multi-layer defense-in-depth orchestrator.

Implements L0-L3 layers with retries and fail-closed behavior.
"""
from uuid import UUID
from fastapi import HTTPException
from app.modules.privacy.privacy_service import get_event
from app.modules.privacy.anonymizer import anonymizer
from app.modules.privacy_v2.layer0_regex import sanitize_preflight
from app.modules.privacy_v2.layer2_verify import verify_anonymization
from app.modules.privacy_v2.layer3_semantic_audit import semantic_audit
from app.modules.privacy_v2.receipts import receipt_manager
from app.modules.privacy_v2.approval_manager import approval_manager
from app.modules.privacy_v2.privacy_v2_status import privacy_v2_status_store
from app.models import PrivacyScrubV2Response, Receipt
from app.core.logging import log_privacy_safe


async def scrub_v2(
    event_id: UUID,
    production_mode: bool,
    max_retries: int = 2
) -> PrivacyScrubV2Response:
    """
    Privacy Shield v2: Multi-layer anonymization with verification.
    
    Args:
        event_id: Event identifier
        production_mode: Production Mode flag (sent in request)
        max_retries: Maximum retry attempts (default 2)
        
    Returns:
        PrivacyScrubV2Response with approval_token if gated
        
    Raises:
        HTTPException: If Production Mode is ON and gated (hard stop)
    """
    # CRITICAL: Get raw text via same pathway as v1 scrub (from in-memory event store)
    event = get_event(event_id)
    raw_text = event.raw_payload  # Same as v1 scrub uses - in-memory only, never persisted
    
    receipt = receipt_manager.create_receipt(event_id)
    
    # Layer 0: Pre-flight sanitization
    receipt_manager.add_step(event_id, "L0", "ok", metrics={"type": "regex_preflight"})
    preflight_text, preflight_metrics = sanitize_preflight(raw_text)
    receipt_manager.add_step(
        event_id, "L0", "ok",
        metrics=preflight_metrics
    )
    
    # Layer 1: Local LLM anonymization (reuse existing anonymizer)
    clean_text = preflight_text  # Start with preflight text
    verification_passed = False
    semantic_risk = False
    
    # CRITICAL: Ensure clean_text is initialized even if all attempts fail
    for attempt in range(max_retries + 1):
        receipt_manager.add_step(
            event_id, f"L1_attempt_{attempt}", "ok",
            model_id="ollama/ministral-3:14b"
        )
        
        try:
            clean_text, mapping, is_anonymized = await anonymizer.anonymize(
                clean_text,
                event_id,
                production_mode
            )
            
            # Layer 2: Post-check verification
            receipt_manager.add_step(event_id, "L2", "ok", metrics={"type": "regex_verification"})
            verification_passed, failures = verify_anonymization(clean_text)
            
            if verification_passed:
                receipt_manager.add_step(event_id, "L2", "ok", metrics={"verification": "passed"})
                break
            else:
                receipt_manager.add_flag(event_id, "verification_failed")
                receipt_manager.add_step(
                    event_id, "L2", "retry",
                    metrics={"failures": failures}
                )
                if attempt < max_retries:
                    continue
                else:
                    receipt_manager.add_step(event_id, "L2", "failed", metrics={"failures": failures})
                    break
        except Exception as e:
            receipt_manager.add_step(event_id, f"L1_attempt_{attempt}", "failed")
            log_privacy_safe(str(event_id), f"L1 anonymization error: {str(e)}")
            if attempt < max_retries:
                continue
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Anonymization failed after {max_retries + 1} attempts"
                )
    
    # Layer 3: Semantic audit (ONLY if verification passed)
    # CRITICAL: Don't waste resources auditing text that failed verification
    if verification_passed:
        receipt_manager.add_step(event_id, "L3", "ok", model_id="ollama/ministral-3b")
        semantic_risk, risk_reason = await semantic_audit(clean_text, str(event_id))
        
        if semantic_risk:
            receipt_manager.add_flag(event_id, "semantic_risk")
            receipt_manager.add_step(
                event_id, "L3", "blocked",
                metrics={"risk_reason": risk_reason}
            )
        else:
            receipt_manager.add_step(event_id, "L3", "ok", metrics={"risk_reason": risk_reason})
    else:
        # If verification failed, assume semantic risk (conservative)
        semantic_risk = True
        risk_reason = "verification_failed"
        receipt_manager.add_flag(event_id, "semantic_risk")
        receipt_manager.add_step(event_id, "L3", "skipped", metrics={"reason": "verification_failed"})
    
    # Gate check
    approval_required = False
    approval_token = None
    gated = not verification_passed or semantic_risk
    
    if gated:
        approval_required = True
        approval_token = approval_manager.generate_token(event_id)
        token_hash = approval_manager.get_token_hash(approval_token)
        receipt_manager.add_step(event_id, "gate", "blocked")
    else:
        receipt_manager.add_step(event_id, "gate", "ok")
    
    # CRITICAL: Store privacy v2 status in RAM (for draft gate to read)
    privacy_v2_status_store.set_status(
        event_id=event_id,
        verification_passed=verification_passed,
        semantic_risk=semantic_risk,
        approval_required=approval_required,
        approval_token_hash=approval_manager.get_token_hash(approval_token) if approval_token else None
    )
    
    # Set clean text hash
    receipt_manager.set_clean_text_hash(event_id, clean_text)
    
    # Final receipt
    final_receipt = receipt_manager.get_receipt(event_id)
    
    # Production Mode enforcement: HARD STOP (no approval in production)
    # CRITICAL: Production Mode = hard stop, not "requires approval"
    if production_mode and gated:
        log_privacy_safe(
            str(event_id),
            "Privacy Shield v2 blocked in Production Mode (HARD STOP)",
            verification_passed=verification_passed,
            semantic_risk=semantic_risk
        )
        raise HTTPException(
            status_code=400,
            detail="Production Mode is ON: verification failed or semantic risk detected. Cannot proceed (hard stop)."
        )
    
    # CRITICAL: is_anonymized must reflect actual verification status
    # If verification failed or semantic risk exists, text is NOT safe for external APIs
    is_anonymized_safe = verification_passed and not semantic_risk
    
    return PrivacyScrubV2Response(
        event_id=event_id,
        clean_text=clean_text,
        is_anonymized=is_anonymized_safe,  # Only True if verification passed AND no semantic risk
        verification_passed=verification_passed,
        semantic_risk=semantic_risk,
        approval_required=approval_required,
        approval_token=approval_token,
        flags=final_receipt.flags if final_receipt else [],
        receipt=final_receipt if final_receipt else Receipt(steps=[], flags=[], clean_text_sha256="")
    )

