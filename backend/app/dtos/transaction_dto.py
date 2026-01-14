"""
Transaction Data Transfer Objects
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    """Transaction information"""
    txid: str
    from_address: Optional[str] = None
    to_address: str
    amount: int
    confirmations: int
    block_height: Optional[int] = None
    detected_at: datetime
    confirmed_at: Optional[datetime] = None
    is_processed: bool
    bet_id: Optional[str] = None


class ManualProcessRequest(BaseModel):
    """Request to manually process a transaction"""
    txid: str
