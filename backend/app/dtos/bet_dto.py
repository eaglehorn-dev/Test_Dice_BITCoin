"""
Bet Data Transfer Objects for API validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class CreateBetRequest(BaseModel):
    """Request to create a bet"""
    multiplier: float = Field(..., gt=1.0, description="Target multiplier")
    bet_amount: Optional[int] = Field(None, gt=0, description="Bet amount in satoshis (optional for address-based bets)")
    
    @validator("multiplier")
    def validate_multiplier(cls, v):
        from app.core.config import config
        if v < config.MIN_MULTIPLIER or v > config.MAX_MULTIPLIER:
            raise ValueError(f"Multiplier must be between {config.MIN_MULTIPLIER} and {config.MAX_MULTIPLIER}")
        return v


class BetResponse(BaseModel):
    """Bet response with result"""
    bet_id: str
    user_address: str
    bet_amount: int
    target_multiplier: float
    win_chance: float
    roll_result: Optional[float] = None
    is_win: Optional[bool] = None
    payout_amount: Optional[int] = None
    profit: Optional[int] = None
    status: str
    nonce: int
    created_at: datetime
    
    # Verification data
    server_seed_hash: str
    client_seed: str


class BetHistoryItem(BaseModel):
    """Single bet in history"""
    bet_id: str  # MongoDB _id (for internal use)
    bet_number: Optional[int] = None  # Incremental bet number (1, 2, 3, ...) - None for old bets
    bet_amount: int
    target_multiplier: float
    multiplier: int
    win_chance: float
    roll_result: float
    is_win: bool
    payout_amount: int
    profit: int
    created_at: datetime
    nonce: int
    target_address: str = None
    deposit_txid: str = None
    payout_txid: Optional[str] = None  # Payout transaction ID (None if bet lost)
    user_address: str = None  # User's Bitcoin address who placed the bet
    server_seed: str = None  # Server seed for provably fair verification
    server_seed_hash: str = None  # Server seed hash shown to user
    client_seed: str = None  # Client seed


class BetHistoryResponse(BaseModel):
    """User bet history"""
    bets: list[BetHistoryItem]
    total_bets: int
    total_wagered: int
    total_won: int
    total_lost: int


class RecentBetsResponse(BaseModel):
    """Recent bets from all users"""
    bets: list[BetHistoryItem]
    count: int
