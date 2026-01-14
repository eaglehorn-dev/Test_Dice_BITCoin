"""
Admin API routes
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.dtos.transaction_dto import ManualProcessRequest
from app.services.bet_service import BetService
from app.services.payout_service import PayoutService
from app.services.transaction_service import TransactionService
from app.core.config import config

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/process-pending-bets")
async def process_pending_bets():
    """Admin endpoint to process pending bets"""
    try:
        bet_service = BetService()
        processed = await bet_service.process_pending_bets()
        
        return {
            "success": True,
            "processed_count": processed,
            "message": f"Processed {processed} bet(s)"
        }
        
    except Exception as e:
        logger.error(f"Error processing pending bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry-payouts")
async def retry_failed_payouts():
    """Admin endpoint to retry failed payouts"""
    try:
        payout_service = PayoutService()
        retried = await payout_service.retry_failed_payouts()
        
        return {
            "success": True,
            "retried_count": retried,
            "message": f"Retried {retried} payout(s)"
        }
        
    except Exception as e:
        logger.error(f"Error retrying payouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manually-process-transaction")
async def manually_process_transaction(request: ManualProcessRequest):
    """
    Admin endpoint to manually process a transaction
    
    Useful for:
    - Processing missed transactions
    - Debugging transaction issues
    - Manual bet creation
    """
    try:
        tx_service = TransactionService()
        bet_service = BetService()
        
        # Verify transaction (will check all vault wallets)
        tx = await tx_service.verify_transaction_for_vault(request.txid)
        
        if not tx:
            raise HTTPException(
                status_code=404, 
                detail="Transaction not found or not sent to any vault wallet"
            )
        
        # Process into bet
        bet = await bet_service.process_detected_transaction(tx)
        
        if not bet:
            raise HTTPException(status_code=400, detail="Failed to create bet from transaction")
        
        return {
            "success": True,
            "transaction_id": request.txid,
            "bet_id": str(bet["_id"]),
            "amount": tx["amount"],
            "target_address": tx.get("target_address"),
            "multiplier": tx.get("multiplier"),
            "status": bet["status"],
            "message": "Transaction processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error manually processing transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
