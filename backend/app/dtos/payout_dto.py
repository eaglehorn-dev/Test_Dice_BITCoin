"""
Payout Data Transfer Objects
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PayoutResponse(BaseModel):
    """Payout information"""
    payout_id: str
    bet_id: str
    amount: int
    to_address: str
    txid: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    network_fee: Optional[int] = None
    retry_count: int
    created_at: datetime
    broadcast_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None


class PayoutStatusResponse(BaseModel):
    """Payout status check"""
    txid: str
    status: str
    confirmations: Optional[int] = None
    block_height: Optional[int] = None
