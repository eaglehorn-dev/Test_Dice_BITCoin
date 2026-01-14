"""
User Repository - Data access for users
"""
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.database import get_users_collection
from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user data access"""
    
    def __init__(self):
        super().__init__(get_users_collection())
    
    async def get_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Get user by Bitcoin address"""
        return await self.find_one({"address": address})
    
    async def create_user(self, address: str) -> Dict[str, Any]:
        """Create new user"""
        user_doc = {
            "address": address,
            "created_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "total_bets": 0,
            "total_wagered": 0,
            "total_won": 0,
            "total_lost": 0
        }
        user_id = await self.insert_one(user_doc)
        user_doc["_id"] = user_id
        return user_doc
    
    async def update_stats(
        self,
        address: str,
        bet_amount: int,
        profit: int,
        is_win: bool
    ) -> bool:
        """Update user statistics after bet"""
        update = {
            "$inc": {
                "total_bets": 1,
                "total_wagered": bet_amount,
                "total_won": profit if is_win else 0,
                "total_lost": abs(profit) if not is_win else 0
            },
            "$set": {
                "last_seen": datetime.utcnow()
            }
        }
        return await self.update_one({"address": address}, update)
    
    async def get_or_create(self, address: str) -> Dict[str, Any]:
        """Get existing user or create new one"""
        user = await self.get_by_address(address)
        if not user:
            user = await self.create_user(address)
        return user
