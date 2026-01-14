"""
Payout model for MongoDB
"""
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import MongoBaseModel, PyObjectId


class PayoutModel(MongoBaseModel):
    """Payout records and tracking"""
    bet_id: PyObjectId
    
    # Payout details
    amount: int  # satoshis
    to_address: str = Field(..., max_length=64)
    txid: Optional[str] = Field(None, max_length=64)
    
    # Status
    status: str = "pending"  # pending, broadcast, confirmed, failed
    error_message: Optional[str] = None
    
    # Fee tracking
    network_fee: Optional[int] = None
    
    # Retry logic
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    broadcast_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
