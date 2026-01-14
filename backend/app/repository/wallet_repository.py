"""
Wallet Repository - Data access for encrypted wallet vault
"""
from typing import Optional, List, Dict, Any
from bson import ObjectId

from .base_repository import BaseRepository
from app.models.database import get_wallets_collection
from app.core.exceptions import DatabaseException


class WalletRepository(BaseRepository):
    """Repository for wallet vault operations"""
    
    def __init__(self):
        super().__init__(get_wallets_collection())
    
    async def find_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Find wallet by Bitcoin address"""
        try:
            return await self.collection.find_one({"address": address})
        except Exception as e:
            raise DatabaseException(f"Error finding wallet by address: {e}")
    
    async def find_by_multiplier(self, multiplier: int, is_active: bool = True) -> Optional[Dict[str, Any]]:
        """
        Find an active wallet for a specific multiplier
        
        Args:
            multiplier: Payout multiplier (e.g., 2, 3, 5)
            is_active: Only return active wallets
            
        Returns:
            Wallet document or None
        """
        try:
            query = {"multiplier": multiplier}
            if is_active:
                query["is_active"] = True
            
            return await self.collection.find_one(query)
        except Exception as e:
            raise DatabaseException(f"Error finding wallet by multiplier: {e}")
    
    async def find_all_by_multiplier(self, multiplier: int) -> List[Dict[str, Any]]:
        """Find all wallets for a specific multiplier"""
        try:
            cursor = self.collection.find({"multiplier": multiplier})
            return await cursor.to_list(length=None)
        except Exception as e:
            raise DatabaseException(f"Error finding wallets by multiplier: {e}")
    
    async def find_active_wallets(self, network: str = None) -> List[Dict[str, Any]]:
        """
        Find all active wallets
        
        Args:
            network: Filter by network (mainnet/testnet), None for all
        """
        try:
            query = {"is_active": True, "is_depleted": False}
            if network:
                query["network"] = network
            
            cursor = self.collection.find(query).sort("multiplier", 1)
            return await cursor.to_list(length=None)
        except Exception as e:
            raise DatabaseException(f"Error finding active wallets: {e}")
    
    async def get_all_multipliers(self, is_active: bool = True) -> List[int]:
        """
        Get list of all available multipliers
        
        Returns:
            List of unique multipliers (e.g., [2, 3, 5, 10, 100])
        """
        try:
            query = {}
            if is_active:
                query["is_active"] = True
            
            multipliers = await self.collection.distinct("multiplier", query)
            return sorted(multipliers)
        except Exception as e:
            raise DatabaseException(f"Error getting multipliers: {e}")
    
    async def update_balance(self, wallet_id: str, balance_satoshis: int) -> bool:
        """Update wallet balance"""
        try:
            from datetime import datetime
            result = await self.collection.update_one(
                {"_id": ObjectId(wallet_id)},
                {
                    "$set": {
                        "balance_satoshis": balance_satoshis,
                        "last_balance_check": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            raise DatabaseException(f"Error updating wallet balance: {e}")
    
    async def increment_stats(
        self,
        wallet_id: str,
        received: int = 0,
        sent: int = 0,
        bet_count: int = 0
    ) -> bool:
        """Increment wallet statistics"""
        try:
            update_data = {}
            if received > 0:
                update_data["total_received"] = received
            if sent > 0:
                update_data["total_sent"] = sent
            if bet_count > 0:
                update_data["bet_count"] = bet_count
            
            if not update_data:
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(wallet_id)},
                {"$inc": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            raise DatabaseException(f"Error incrementing wallet stats: {e}")
    
    async def mark_depleted(self, wallet_id: str, is_depleted: bool = True) -> bool:
        """Mark wallet as depleted (insufficient funds)"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(wallet_id)},
                {"$set": {"is_depleted": is_depleted}}
            )
            return result.modified_count > 0
        except Exception as e:
            raise DatabaseException(f"Error marking wallet depleted: {e}")
