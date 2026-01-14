"""
Bet model for MongoDB
"""
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import MongoBaseModel, PyObjectId


class BetModel(MongoBaseModel):
    """Individual bet records"""
    user_id: PyObjectId
    seed_id: PyObjectId
    
    # Bet details
    bet_amount: int  # satoshis
    target_multiplier: float
    win_chance: float  # percentage
    
    # Result
    nonce: int
    roll_result: Optional[float] = None  # 0.00 - 99.99
    is_win: Optional[bool] = None
    payout_amount: Optional[int] = None  # satoshis
    profit: Optional[int] = None  # satoshis (can be negative)
    
    # Transaction tracking
    deposit_txid: Optional[str] = Field(None, max_length=64)
    deposit_address: Optional[str] = Field(None, max_length=64)
    payout_txid: Optional[str] = Field(None, max_length=64)
    
    # Status tracking
    status: str = "pending"  # pending, confirmed, rolled, paid, failed
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    rolled_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
