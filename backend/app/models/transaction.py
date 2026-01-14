"""
Transaction model for MongoDB
"""
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import MongoBaseModel, PyObjectId


class TransactionModel(MongoBaseModel):
    """Transaction detection and state tracking"""
    txid: str = Field(..., max_length=64)
    bet_id: Optional[PyObjectId] = None
    
    # Transaction details
    from_address: Optional[str] = Field(None, max_length=64)
    to_address: str = Field(..., max_length=64)
    amount: int  # satoshis
    fee: Optional[int] = None
    
    # Detection metadata
    detected_by: str  # websocket, manual, api
    detection_count: int = 1  # how many times we detected this
    
    # Blockchain status
    confirmations: int = 0
    block_height: Optional[int] = None
    block_hash: Optional[str] = Field(None, max_length=64)
    
    # State tracking
    is_processed: bool = False
    is_duplicate: bool = False
    
    # Timestamps
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # Raw data for debugging
    raw_data: Optional[str] = None  # JSON string
