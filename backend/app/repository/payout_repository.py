"""
Payout Repository - Data access for payouts
"""
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime

from app.models.database import get_payouts_collection
from .base_repository import BaseRepository


class PayoutRepository(BaseRepository):
    """Repository for payout data access"""
    
    def __init__(self):
        super().__init__(get_payouts_collection())
    
    async def get_by_bet_id(self, bet_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get payout by bet ID"""
        return await self.find_one({"bet_id": bet_id})
    
    async def get_by_txid(self, txid: str) -> Optional[Dict[str, Any]]:
        """Get payout by transaction ID"""
        return await self.find_one({"txid": txid})
    
    async def get_failed_payouts(self) -> List[Dict[str, Any]]:
        """Get failed payouts that can be retried"""
        return await self.find_many(
            {
                "status": {"$in": ["pending", "failed"]},
                "$expr": {"$lt": ["$retry_count", "$max_retries"]}
            },
            limit=100
        )
    
    async def get_broadcast_payouts(self) -> List[Dict[str, Any]]:
        """Get payouts that are broadcast but not confirmed"""
        return await self.find_many(
            {
                "status": "broadcast",
                "txid": {"$ne": None, "$exists": True}
            },
            limit=100
        )
    
    async def update_status(
        self,
        payout_id: ObjectId,
        status: str,
        **kwargs
    ) -> bool:
        """Update payout status"""
        update_data = {"status": status}
        
        # Add timestamp based on status
        if status == "broadcast":
            update_data["broadcast_at"] = datetime.utcnow()
        elif status == "confirmed":
            update_data["confirmed_at"] = datetime.utcnow()
        
        # Add any additional fields
        update_data.update(kwargs)
        
        return await self.update_by_id(payout_id, {"$set": update_data})
    
    async def increment_retry_count(self, payout_id: ObjectId) -> bool:
        """Increment retry count"""
        return await self.update_by_id(
            payout_id,
            {"$inc": {"retry_count": 1}}
        )
