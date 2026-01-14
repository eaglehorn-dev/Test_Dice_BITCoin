"""
Bet-related API routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from bson import ObjectId
from loguru import logger

from app.dtos.bet_dto import BetResponse, BetHistoryResponse, BetHistoryItem, RecentBetsResponse
from app.models.database import get_bets_collection, get_seeds_collection, get_users_collection
from app.services.provably_fair_service import ProvablyFairService

router = APIRouter(prefix="/api/bets", tags=["bets"])


@router.get("/history/{address}", response_model=BetHistoryResponse)
async def get_bet_history(
    address: str,
    limit: int = Query(default=50, le=100, description="Number of bets to return")
):
    """
    Get betting history for a specific user address
    
    Args:
        address: User's Bitcoin address
        limit: Maximum number of bets to return (max 100)
    """
    try:
        users_col = get_users_collection()
        bets_col = get_bets_collection()
        
        user = await users_col.find_one({"address": address})
        if not user:
            return BetHistoryResponse(
                bets=[],
                total_bets=0,
                total_wagered=0,
                total_won=0,
                total_lost=0
            )
        
        bets = await bets_col.find(
            {"user_id": user["_id"], "roll_result": {"$ne": None}}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        bet_items = [
            BetHistoryItem(
                bet_id=str(bet["_id"]),
                bet_amount=bet["bet_amount"],
                target_multiplier=bet["target_multiplier"],
                win_chance=bet["win_chance"],
                roll_result=bet["roll_result"],
                is_win=bet["is_win"],
                payout_amount=bet["payout_amount"],
                profit=bet["profit"],
                created_at=bet["created_at"],
                nonce=bet["nonce"]
            )
            for bet in bets
        ]
        
        return BetHistoryResponse(
            bets=bet_items,
            total_bets=user.get("total_bets", 0),
            total_wagered=user.get("total_wagered", 0),
            total_won=user.get("total_won", 0),
            total_lost=user.get("total_lost", 0)
        )
        
    except Exception as e:
        logger.error(f"Error getting bet history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=RecentBetsResponse)
async def get_recent_bets(
    limit: int = Query(default=50, le=100, description="Number of bets to return")
):
    """
    Get recent bets from all users
    
    Args:
        limit: Maximum number of bets to return (max 100)
    """
    try:
        bets_col = get_bets_collection()
        
        # Get recent completed bets
        bets = await bets_col.find(
            {"roll_result": {"$ne": None}}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        # Format response
        bet_items = [
            BetHistoryItem(
                bet_id=str(bet["_id"]),
                bet_amount=bet["bet_amount"],
                target_multiplier=bet["target_multiplier"],
                win_chance=bet["win_chance"],
                roll_result=bet["roll_result"],
                is_win=bet["is_win"],
                payout_amount=bet["payout_amount"],
                profit=bet["profit"],
                created_at=bet["created_at"],
                nonce=bet["nonce"]
            )
            for bet in bets
        ]
        
        return RecentBetsResponse(
            bets=bet_items,
            count=len(bet_items)
        )
        
    except Exception as e:
        logger.error(f"Error getting recent bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{bet_id}", response_model=BetResponse)
async def get_bet_details(bet_id: str):
    """
    Get details for a specific bet
    
    Args:
        bet_id: Bet ID
    """
    try:
        if not ObjectId.is_valid(bet_id):
            raise HTTPException(status_code=400, detail="Invalid bet ID")
        
        bets_col = get_bets_collection()
        users_col = get_users_collection()
        seeds_col = get_seeds_collection()
        
        bet = await bets_col.find_one({"_id": ObjectId(bet_id)})
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        user = await users_col.find_one({"_id": bet["user_id"]})
        seed = await seeds_col.find_one({"_id": bet["seed_id"]})
        
        return BetResponse(
            bet_id=str(bet["_id"]),
            user_address=user["address"] if user else "Unknown",
            bet_amount=bet["bet_amount"],
            target_multiplier=bet["target_multiplier"],
            win_chance=bet["win_chance"],
            roll_result=bet.get("roll_result"),
            is_win=bet.get("is_win"),
            payout_amount=bet.get("payout_amount"),
            profit=bet.get("profit"),
            status=bet["status"],
            nonce=bet["nonce"],
            created_at=bet["created_at"],
            server_seed_hash=seed["server_seed_hash"] if seed else "",
            client_seed=seed["client_seed"] if seed else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bet details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
