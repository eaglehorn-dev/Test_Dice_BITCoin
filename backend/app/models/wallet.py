"""
Wallet Model - Encrypted Bitcoin Wallet Storage
"""
from datetime import datetime
from typing import Optional
from pydantic import Field

from .base import MongoBaseModel, PyObjectId


class WalletModel(MongoBaseModel):
    """
    Encrypted Bitcoin wallet for multiplier-based payouts
    
    Security:
    - private_key is ALWAYS encrypted (Fernet/AES-256)
    - private_key_encrypted field name makes it explicit
    - Never store unencrypted keys in database
    """
    
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    multiplier: int = Field(..., description="Payout multiplier (2, 3, 4, 5, 10, 100, etc)")
    address: str = Field(..., description="Bitcoin address (public)")
    private_key_encrypted: str = Field(..., description="Encrypted private key (WIF)")
    
    network: str = Field(default="mainnet", description="Bitcoin network (mainnet/testnet)")
    address_type: str = Field(default="P2WPKH", description="Address type (P2PKH/P2WPKH)")
    
    is_active: bool = Field(default=True, description="Whether wallet is available for new bets")
    is_depleted: bool = Field(default=False, description="Wallet has insufficient funds")
    
    total_received: int = Field(default=0, description="Total satoshis received")
    total_sent: int = Field(default=0, description="Total satoshis sent")
    bet_count: int = Field(default=0, description="Number of bets using this wallet")
    
    balance_satoshis: int = Field(default=0, description="Cached balance (updated periodically)")
    last_balance_check: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    label: Optional[str] = Field(None, description="Human-readable label (e.g., '3x Multiplier Wallet')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "multiplier": 3,
                "address": "bc1q...",
                "private_key_encrypted": "gAAAAA...[encrypted]",
                "network": "mainnet",
                "is_active": True,
                "label": "3x Multiplier Wallet"
            }
        }
