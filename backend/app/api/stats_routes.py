"""
Statistics API routes
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.dtos.stats_dto import UserStatsResponse, GameStatsResponse
from app.models.database import get_users_collection, get_bets_collection, get_payouts_collection
from app.core.config import config

router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("/user/{address}", response_model=UserStatsResponse)
async def get_user_stats(address: str):
    """
    Get statistics for a specific user
    
    Args:
        address: User's Bitcoin address
    """
    try:
        users_col = get_users_collection()
        user = await users_col.find_one({"address": address})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        total_wagered = user.get("total_wagered", 0)
        total_won = user.get("total_won", 0)
        total_lost = user.get("total_lost", 0)
        total_bets = user.get("total_bets", 0)
        
        # Calculate win rate
        bets_col = get_bets_collection()
        completed_bets = await bets_col.count_documents({
            "user_id": user["_id"],
            "roll_result": {"$ne": None}
        })
        
        wins = await bets_col.count_documents({
            "user_id": user["_id"],
            "is_win": True
        })
        
        win_rate = (wins / completed_bets * 100) if completed_bets > 0 else 0
        
        return UserStatsResponse(
            address=address,
            total_bets=total_bets,
            total_wagered=total_wagered,
            total_won=total_won,
            total_lost=total_lost,
            net_profit=total_won - total_lost,
            win_rate=round(win_rate, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game", response_model=GameStatsResponse)
async def get_game_stats():
    """Get overall game statistics"""
    try:
        users_col = get_users_collection()
        bets_col = get_bets_collection()
        payouts_col = get_payouts_collection()
        
        # Count users and bets
        total_users = await users_col.count_documents({})
        total_bets = await bets_col.count_documents({"roll_result": {"$ne": None}})
        active_bets = await bets_col.count_documents({"status": {"$in": ["pending", "confirmed"]}})
        pending_payouts = await payouts_col.count_documents({"status": {"$in": ["pending", "failed"]}})
        
        # Calculate totals using aggregation
        pipeline_wagered = [
            {"$match": {"roll_result": {"$ne": None}}},
            {"$group": {"_id": None, "total": {"$sum": "$bet_amount"}}}
        ]
        
        pipeline_paid = [
            {"$match": {"is_win": True}},
            {"$group": {"_id": None, "total": {"$sum": "$payout_amount"}}}
        ]
        
        wagered_result = await bets_col.aggregate(pipeline_wagered).to_list(length=1)
        paid_result = await bets_col.aggregate(pipeline_paid).to_list(length=1)
        
        total_wagered = wagered_result[0]["total"] if wagered_result else 0
        total_paid_out = paid_result[0]["total"] if paid_result else 0
        house_profit = total_wagered - total_paid_out
        
        return GameStatsResponse(
            total_bets=total_bets,
            total_users=total_users,
            total_wagered=total_wagered,
            total_paid_out=total_paid_out,
            house_profit=house_profit,
            active_bets=active_bets,
            pending_payouts=pending_payouts
        )
        
    except Exception as e:
        logger.error(f"Error getting game stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/house")
async def get_house_info():
    """Get vault system information"""
    try:
        from app.services.wallet_service import WalletService
        
        wallet_service = WalletService()
        active_wallets = await wallet_service.get_active_wallets()
        available_multipliers = await wallet_service.get_available_multipliers()
        
        # Format wallet info (public data only)
        wallets_info = []
        for wallet in active_wallets:
            wallets_info.append({
                "multiplier": wallet["multiplier"],
                "address": wallet["address"],
                "label": wallet.get("label", f"{wallet['multiplier']}x Wallet"),
                "is_active": wallet.get("is_active", True)
            })
        
        return {
            "network": config.NETWORK,
            "house_edge": config.HOUSE_EDGE,
            "min_bet": config.MIN_BET_SATOSHIS,
            "max_bet": config.MAX_BET_SATOSHIS,
            "min_multiplier": config.MIN_MULTIPLIER,
            "max_multiplier": config.MAX_MULTIPLIER,
            "vault_system": {
                "total_wallets": len(active_wallets),
                "available_multipliers": sorted(available_multipliers),
                "wallets": sorted(wallets_info, key=lambda x: x["multiplier"])
            }
        }
    except Exception as e:
        logger.error(f"Error getting house info: {e}")
        # Fallback response
        return {
            "network": config.NETWORK,
            "house_edge": config.HOUSE_EDGE,
            "min_bet": config.MIN_BET_SATOSHIS,
            "max_bet": config.MAX_BET_SATOSHIS,
            "min_multiplier": config.MIN_MULTIPLIER,
            "max_multiplier": config.MAX_MULTIPLIER,
            "vault_system": {
                "total_wallets": 0,
                "available_multipliers": [],
                "wallets": []
            }
        }
