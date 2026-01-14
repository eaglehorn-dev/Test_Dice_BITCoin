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
    bet_amount: int
    target_multiplier: float
    win_chance: float
    multiplier: int = Field(..., description="Wallet multiplier (2x, 3x, etc.)")
    
    # Result
    nonce: int
    roll_result: Optional[float] = None
    is_win: Optional[bool] = None
    payout_amount: Optional[int] = None
    profit: Optional[int] = None
    
    # Transaction tracking
    deposit_txid: Optional[str] = Field(None, max_length=64)
    deposit_address: Optional[str] = Field(None, max_length=64)
    target_address: str = Field(..., description="Wallet address user sent BTC to")
    wallet_id: Optional[PyObjectId] = Field(None, description="Vault wallet used for payout")
    payout_txid: Optional[str] = Field(None, max_length=64)
    
    # Status tracking
    status: str = "pending"  # pending, confirmed, rolled, paid, failed
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    rolled_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
