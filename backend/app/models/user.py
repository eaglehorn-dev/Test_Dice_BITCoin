"""
User model for MongoDB
"""
from datetime import datetime
from pydantic import Field
from .base import MongoBaseModel


class UserModel(MongoBaseModel):
    """User accounts and wallet addresses"""
    address: str = Field(..., max_length=64)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Statistics
    total_bets: int = 0
    total_wagered: int = 0  # in satoshis
    total_won: int = 0
    total_lost: int = 0
