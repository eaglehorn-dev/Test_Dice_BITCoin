"""
Seed model for provably fair system
"""
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import MongoBaseModel, PyObjectId


class SeedModel(MongoBaseModel):
    """Server and client seeds for provably fair system"""
    user_id: PyObjectId
    
    # Server seed (hidden until reveal)
    server_seed: str = Field(..., max_length=128)
    server_seed_hash: str = Field(..., max_length=128)  # SHA256 hash shown to user
    
    # Client seed
    client_seed: str = Field(..., max_length=128)
    
    # Nonce counter
    nonce: int = 0
    
    # Status
    is_active: bool = True
    revealed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
