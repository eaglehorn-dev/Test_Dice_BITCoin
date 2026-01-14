"""
Bet Repository - Data access for bets
"""
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime

from app.models.database import get_bets_collection
from .base_repository import BaseRepository


class BetRepository(BaseRepository):
    """Repository for bet data access"""
    
    def __init__(self):
        super().__init__(get_bets_collection())
    
    async def get_by_deposit_txid(self, txid: str) -> Optional[Dict[str, Any]]:
        """Get bet by deposit transaction ID"""
        return await self.find_one({"deposit_txid": txid})
    
    async def get_by_user(
        self,
        user_id: ObjectId,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get bets for a specific user"""
        return await self.find_many(
            {"user_id": user_id},
            limit=limit,
            skip=skip,
            sort=[("created_at", -1)]
        )
    
    async def get_recent_bets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent bets from all users"""
        return await self.find_many(
            {"roll_result": {"$ne": None}},
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    async def get_pending_bets(self) -> List[Dict[str, Any]]:
        """Get all pending bets"""
        return await self.find_many(
            {
                "status": {"$in": ["pending", "confirmed"]},
                "roll_result": None
            },
            limit=1000
        )
    
    async def update_status(
        self,
        bet_id: ObjectId,
        status: str,
        **kwargs
    ) -> bool:
        """Update bet status"""
        update_data = {"status": status}
        
        # Add timestamp based on status
        if status == "confirmed":
            update_data["confirmed_at"] = datetime.utcnow()
        elif status == "rolled":
            update_data["rolled_at"] = datetime.utcnow()
        elif status == "paid":
            update_data["paid_at"] = datetime.utcnow()
        
        # Add any additional fields
        update_data.update(kwargs)
        
        return await self.update_by_id(bet_id, {"$set": update_data})
    
    async def update_result(
        self,
        bet_id: ObjectId,
        roll_result: float,
        is_win: bool,
        payout_amount: int,
        profit: int
    ) -> bool:
        """Update bet with roll result"""
        update_data = {
            "roll_result": roll_result,
            "is_win": is_win,
            "payout_amount": payout_amount,
            "profit": profit,
            "rolled_at": datetime.utcnow(),
            "status": "rolled"
        }
        return await self.update_by_id(bet_id, {"$set": update_data})
