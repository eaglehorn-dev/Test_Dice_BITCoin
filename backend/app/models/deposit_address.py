"""
Deposit address model for MongoDB
"""
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import MongoBaseModel, PyObjectId


class DepositAddressModel(MongoBaseModel):
    """Generated deposit addresses for users"""
    user_id: PyObjectId
    
    # Address details
    address: str = Field(..., max_length=64)
    derivation_path: Optional[str] = Field(None, max_length=50)  # For HD wallets
    
    # Status
    is_active: bool = True
    is_used: bool = False
    
    # Expected bet parameters (optional)
    expected_multiplier: Optional[float] = None
    expected_amount_min: Optional[int] = None
    expected_amount_max: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
