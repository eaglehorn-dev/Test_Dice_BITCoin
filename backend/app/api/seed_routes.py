"""
Provably fair seed management routes
"""
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from loguru import logger

from app.models.database import get_seeds_collection
from app.services.provably_fair_service import ProvablyFairService

router = APIRouter(prefix="/api/seeds", tags=["provably-fair"])


@router.get("/verify/{seed_id}")
async def verify_seed(seed_id: str):
    """
    Get verification data for a seed
    
    Args:
        seed_id: Seed ID
    """
    try:
        if not ObjectId.is_valid(seed_id):
            raise HTTPException(status_code=400, detail="Invalid seed ID")
        
        seeds_col = get_seeds_collection()
        seed = await seeds_col.find_one({"_id": ObjectId(seed_id)})
        
        if not seed:
            raise HTTPException(status_code=404, detail="Seed not found")
        
        # Only reveal if seed is inactive
        if seed["is_active"]:
            return {
                "server_seed_hash": seed["server_seed_hash"],
                "client_seed": seed["client_seed"],
                "nonce": seed["nonce"],
                "is_active": True,
                "message": "Server seed is still active and cannot be revealed yet"
            }
        
        # Return full verification data for inactive seeds
        return {
            "server_seed": seed["server_seed"],
            "server_seed_hash": seed["server_seed_hash"],
            "client_seed": seed["client_seed"],
            "nonce": seed["nonce"],
            "is_active": False,
            "revealed_at": seed.get("revealed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying seed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-bet")
async def verify_bet_fairness(
    server_seed: str,
    client_seed: str,
    nonce: int,
    roll: float
):
    """
    Verify a bet's fairness
    
    Args:
        server_seed: Revealed server seed
        client_seed: Client seed
        nonce: Nonce used
        roll: Roll result to verify
    """
    try:
        fair_service = ProvablyFairService()
        
        # Calculate expected roll
        calculated_roll = fair_service.calculate_roll(server_seed, client_seed, nonce)
        
        # Check if matches
        is_valid = abs(calculated_roll - roll) < 0.01
        
        return {
            "is_valid": is_valid,
            "provided_roll": roll,
            "calculated_roll": calculated_roll,
            "server_seed": server_seed,
            "client_seed": client_seed,
            "nonce": nonce,
            "message": "Roll is valid" if is_valid else "Roll verification failed"
        }
        
    except Exception as e:
        logger.error(f"Error verifying bet fairness: {e}")
        raise HTTPException(status_code=500, detail=str(e))
