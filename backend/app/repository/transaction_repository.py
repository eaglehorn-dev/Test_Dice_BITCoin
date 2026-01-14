"""
Transaction Repository - Data access for transactions
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.database import get_transactions_collection
from .base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for transaction data access"""
    
    def __init__(self):
        super().__init__(get_transactions_collection())
    
    async def get_by_txid(self, txid: str) -> Optional[Dict[str, Any]]:
        """Get transaction by txid"""
        return await self.find_one({"txid": txid})
    
    async def get_unprocessed(self) -> List[Dict[str, Any]]:
        """Get all unprocessed transactions"""
        return await self.find_many(
            {"is_processed": False},
            limit=1000,
            sort=[("detected_at", 1)]
        )
    
    async def mark_processed(self, txid: str, bet_id=None) -> bool:
        """Mark transaction as processed"""
        update_data = {
            "is_processed": True,
            "processed_at": datetime.utcnow()
        }
        if bet_id:
            update_data["bet_id"] = bet_id
        
        return await self.update_one(
            {"txid": txid},
            {"$set": update_data}
        )
    
    async def increment_detection_count(self, txid: str) -> bool:
        """Increment detection count for duplicate detection"""
        return await self.update_one(
            {"txid": txid},
            {"$inc": {"detection_count": 1}}
        )
