"""
Bet verification API routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from loguru import logger

from app.models.database import get_bets_collection
from app.services.provably_fair_service import ProvablyFairService

router = APIRouter(prefix="/api/bet", tags=["bet"])


class VerifyBetRequest(BaseModel):
    """Request model for bet verification"""
    bet_id: int  # Bet number (incremental ID)


class VerifyBetResponse(BaseModel):
    """Response model for bet verification"""
    is_valid: bool
    bet_id: str
    bet_number: int
    nonce: int
    roll: float
    server_seed: str
    server_seed_hash: str
    client_seed: str
    verification_data: dict


@router.post("/verify", response_model=VerifyBetResponse)
async def verify_bet(request: VerifyBetRequest):
    """
    Verify a bet's provably fair result
    
    Args:
        request: VerifyBetRequest with bet_id (bet_number)
        
    Returns:
        VerifyBetResponse with verification results
    """
    try:
        bets_col = get_bets_collection()
        
        # Try to find bet by bet_number first (incremental ID)
        bet = await bets_col.find_one({"bet_number": request.bet_id})
        
        # If not found by bet_number, try MongoDB _id (for backward compatibility)
        if not bet:
            try:
                if ObjectId.is_valid(str(request.bet_id)):
                    bet = await bets_col.find_one({"_id": ObjectId(str(request.bet_id))})
            except:
                pass
        
        if not bet:
            raise HTTPException(status_code=404, detail=f"Bet {request.bet_id} not found")
        
        # Check if bet has been rolled
        if bet.get("roll_result") is None:
            raise HTTPException(status_code=400, detail="Bet has not been rolled yet")
        
        # Get required fields
        server_seed = bet.get("server_seed")
        server_seed_hash = bet.get("server_seed_hash")
        client_seed = bet.get("client_seed")
        nonce = bet.get("nonce")
        roll_result = bet.get("roll_result")
        
        if not server_seed:
            raise HTTPException(status_code=400, detail="Server seed not found in bet record")
        if not server_seed_hash:
            raise HTTPException(status_code=400, detail="Server seed hash not found in bet record")
        if not client_seed:
            raise HTTPException(status_code=400, detail="Client seed not found in bet record")
        if nonce is None:
            raise HTTPException(status_code=400, detail="Nonce not found in bet record")
        if roll_result is None:
            raise HTTPException(status_code=400, detail="Roll result not found in bet record")
        
        # Generate verification data
        verification_data = ProvablyFairService.generate_verification_data(
            server_seed=server_seed,
            server_seed_hash=server_seed_hash,
            client_seed=client_seed,
            nonce=nonce,
            roll=roll_result
        )
        
        # Return verification response
        return VerifyBetResponse(
            is_valid=verification_data["overall_valid"],
            bet_id=str(bet["_id"]),
            bet_number=bet.get("bet_number", 0),
            nonce=nonce,
            roll=roll_result,
            server_seed=server_seed,
            server_seed_hash=server_seed_hash,
            client_seed=client_seed,
            verification_data=verification_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying bet {request.bet_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error verifying bet: {str(e)}")
