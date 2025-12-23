"""
Receipt system for transparency.

Receipts track all steps in privacy processing. Never persist, RAM-only TTL.
"""
import hashlib
import time
from typing import Dict, Optional
from uuid import UUID
from app.models import Receipt, ReceiptStep
from datetime import datetime


class ReceiptManager:
    """Manages receipts in RAM with TTL."""
    
    def __init__(self, ttl_seconds: int = 900):  # 15 min default
        self._receipts: Dict[UUID, Receipt] = {}
        self._timestamps: Dict[UUID, float] = {}
        self.ttl = ttl_seconds
    
    def create_receipt(self, event_id: UUID) -> Receipt:
        """Create new receipt for event."""
        receipt = Receipt(
            steps=[],
            flags=[],
            clean_text_sha256=""
        )
        self._receipts[event_id] = receipt
        self._timestamps[event_id] = time.time()
        return receipt
    
    def get_receipt(self, event_id: UUID) -> Optional[Receipt]:
        """Get receipt if exists and not expired."""
        if event_id not in self._receipts:
            return None
        if time.time() - self._timestamps[event_id] > self.ttl:
            self._receipts.pop(event_id, None)
            self._timestamps.pop(event_id, None)
            return None
        return self._receipts[event_id]
    
    def add_step(
        self,
        event_id: UUID,
        name: str,
        status: str,
        model_id: Optional[str] = None,
        metrics: Dict = None
    ):
        """Add step to receipt."""
        receipt = self.get_receipt(event_id)
        if not receipt:
            receipt = self.create_receipt(event_id)
        
        step = ReceiptStep(
            name=name,
            status=status,
            model_id=model_id,
            started_at=datetime.utcnow().isoformat(),
            ended_at=datetime.utcnow().isoformat(),
            metrics=metrics or {}
        )
        receipt.steps.append(step)
    
    def add_flag(self, event_id: UUID, flag: str):
        """Add flag to receipt."""
        receipt = self.get_receipt(event_id)
        if not receipt:
            receipt = self.create_receipt(event_id)
        if flag not in receipt.flags:
            receipt.flags.append(flag)
    
    def set_clean_text_hash(self, event_id: UUID, clean_text: str):
        """Set SHA256 hash of clean text."""
        receipt = self.get_receipt(event_id)
        if not receipt:
            receipt = self.create_receipt(event_id)
        receipt.clean_text_sha256 = hashlib.sha256(clean_text.encode()).hexdigest()


receipt_manager = ReceiptManager()

