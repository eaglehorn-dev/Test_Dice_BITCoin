"""
Analytics Service
MongoDB aggregation pipelines for admin dashboard statistics
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger
from app.utils.database import get_bets_collection, get_payouts_collection

class AnalyticsService:
    """Service for calculating statistics and analytics"""
    
    def __init__(self):
        self.bets_collection = get_bets_collection()
        self.payouts_collection = get_payouts_collection()
    
    async def get_income_outcome_stats(self, period: str = "today") -> Dict[str, Any]:
        """
        Calculate Income (bets received) vs Outcome (payouts sent)
        Periods: today, week, month, year, all
        """
        start_date = self._get_period_start_date(period)
        
        match_filter = {}
        if start_date:
            match_filter["created_at"] = {"$gte": start_date}
        
        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": None,
                    "total_bets": {"$sum": 1},
                    "total_income": {"$sum": "$bet_amount"},
                    "total_payout": {"$sum": {"$cond": ["$is_win", "$payout_amount", 0]}},
                    "total_wins": {"$sum": {"$cond": ["$is_win", 1, 0]}},
                    "total_losses": {"$sum": {"$cond": [{"$eq": ["$is_win", False]}, 1, 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_bets": 1,
                    "total_income": 1,
                    "total_payout": 1,
                    "net_profit": {"$subtract": ["$total_income", "$total_payout"]},
                    "total_wins": 1,
                    "total_losses": 1,
                    "win_rate": {
                        "$multiply": [
                            {"$divide": ["$total_wins", {"$cond": [{"$gt": ["$total_bets", 0]}, "$total_bets", 1]}]},
                            100
                        ]
                    }
                }
            }
        ]
        
        result = await self.bets_collection.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "total_bets": 0,
                "total_income": 0,
                "total_payout": 0,
                "net_profit": 0,
                "total_wins": 0,
                "total_losses": 0,
                "win_rate": 0.0
            }
        
        return result[0]
    
    async def get_volume_by_multiplier(self, period: str = "all") -> List[Dict[str, Any]]:
        """Get bet volume grouped by multiplier"""
        start_date = self._get_period_start_date(period)
        
        match_filter = {}
        if start_date:
            match_filter["created_at"] = {"$gte": start_date}
        
        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": "$multiplier",
                    "bet_count": {"$sum": 1},
                    "total_wagered": {"$sum": "$bet_amount"},
                    "total_paid_out": {"$sum": {"$cond": ["$is_win", "$payout_amount", 0]}},
                    "wins": {"$sum": {"$cond": ["$is_win", 1, 0]}},
                }
            },
            {
                "$project": {
                    "multiplier": "$_id",
                    "bet_count": 1,
                    "total_wagered": 1,
                    "total_paid_out": 1,
                    "wins": 1,
                    "profit": {"$subtract": ["$total_wagered", "$total_paid_out"]},
                    "_id": 0
                }
            },
            {"$sort": {"multiplier": 1}}
        ]
        
        results = await self.bets_collection.aggregate(pipeline).to_list(length=None)
        return results
    
    async def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily statistics for the last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                    },
                    "bets": {"$sum": 1},
                    "income": {"$sum": "$bet_amount"},
                    "payout": {"$sum": {"$cond": ["$is_win", "$payout_amount", 0]}},
                    "wins": {"$sum": {"$cond": ["$is_win", 1, 0]}},
                }
            },
            {
                "$project": {
                    "date": "$_id",
                    "bets": 1,
                    "income": 1,
                    "payout": 1,
                    "profit": {"$subtract": ["$income", "$payout"]},
                    "wins": 1,
                    "_id": 0
                }
            },
            {"$sort": {"date": 1}}
        ]
        
        results = await self.bets_collection.aggregate(pipeline).to_list(length=None)
        return results
    
    async def get_top_bets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top bets by amount"""
        pipeline = [
            {"$sort": {"bet_amount": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "bet_id": {"$toString": "$_id"},
                    "bet_amount": 1,
                    "multiplier": 1,
                    "is_win": 1,
                    "payout_amount": 1,
                    "target_address": 1,
                    "deposit_txid": 1,
                    "created_at": 1,
                    "_id": 0
                }
            }
        ]
        
        results = await self.bets_collection.aggregate(pipeline).to_list(length=limit)
        return results
    
    def _get_period_start_date(self, period: str) -> datetime | None:
        """Get start date for period filter"""
        now = datetime.utcnow()
        
        if period == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            return now - timedelta(days=7)
        elif period == "month":
            return now - timedelta(days=30)
        elif period == "year":
            return now - timedelta(days=365)
        else:  # "all"
            return None
