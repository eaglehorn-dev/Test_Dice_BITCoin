"""
FastAPI Main Application
REST API for Bitcoin Dice Game
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from .config import config
from .database import get_db, init_db, User, Bet, Seed, Transaction, Payout, DepositAddress
from .provably_fair import ProvablyFair, generate_new_seed_pair
from .blockchain import TransactionDetector, TransactionMonitor
from .payout import PayoutEngine, BetProcessor

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE) if config.ENABLE_LOGGING else logging.NullHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global transaction monitor
tx_monitor = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("[STARTUP] Starting Bitcoin Dice Game API")
    
    # Validate configuration
    try:
        config.validate()
        logger.info("[OK] Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise
    
    # Initialize database
    init_db()
    logger.info("[OK] Database initialized")
    
    # Start transaction monitor
    global tx_monitor
    tx_monitor = TransactionMonitor()
    asyncio.create_task(tx_monitor.start())
    logger.info("[OK] Transaction monitor started")
    
    yield
    
    # Shutdown
    logger.info("[SHUTDOWN] Shutting down Bitcoin Dice Game API")
    if tx_monitor:
        tx_monitor.stop()


# Create FastAPI app
app = FastAPI(
    title="Bitcoin Dice Game API",
    description="Provably Fair Bitcoin Dice Game with Multi-Layer Transaction Detection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class UserResponse(BaseModel):
    id: int
    address: str
    total_bets: int
    total_wagered: int
    total_won: int
    total_lost: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SeedResponse(BaseModel):
    id: int
    server_seed_hash: str
    client_seed: str
    nonce: int
    is_active: bool
    revealed: bool = False
    server_seed: Optional[str] = None
    
    class Config:
        from_attributes = True


class BetResponse(BaseModel):
    id: int
    bet_amount: int
    target_multiplier: float
    win_chance: float
    roll_result: Optional[float]
    is_win: Optional[bool]
    payout_amount: Optional[int]
    profit: Optional[int]
    status: str
    deposit_txid: Optional[str]
    payout_txid: Optional[str]
    created_at: datetime
    rolled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CreateDepositRequest(BaseModel):
    user_address: str = Field(..., description="User's Bitcoin address")
    multiplier: float = Field(2.0, ge=config.MIN_MULTIPLIER, le=config.MAX_MULTIPLIER)


class CreateDepositResponse(BaseModel):
    deposit_address: str
    multiplier: float
    min_amount: int
    max_amount: int
    expires_at: Optional[datetime]


class SubmitTxRequest(BaseModel):
    txid: str = Field(..., description="Transaction ID")
    deposit_address: str = Field(..., description="Deposit address")


class VerifyBetRequest(BaseModel):
    bet_id: int


class VerificationResponse(BaseModel):
    bet_id: int
    server_seed: str
    server_seed_hash: str
    client_seed: str
    nonce: int
    roll: float
    is_valid: bool
    verification_data: dict


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "name": "Bitcoin Dice Game API",
        "version": "1.0.0",
        "network": config.NETWORK
    }


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get global statistics"""
    try:
        total_users = db.query(User).count()
        total_bets = db.query(Bet).count()
        total_wagered = db.query(Bet).filter(Bet.bet_amount.isnot(None)).count()
        
        # Calculate win rate
        total_wins = db.query(Bet).filter(Bet.is_win == True).count()
        win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
        
        return {
            "total_users": total_users,
            "total_bets": total_bets,
            "total_wagered": total_wagered,
            "win_rate": round(win_rate, 2),
            "house_edge": config.HOUSE_EDGE * 100,
            "min_bet": config.MIN_BET_SATOSHIS,
            "max_bet": config.MAX_BET_SATOSHIS
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/user/connect")
async def connect_user(user_address: str, db: Session = Depends(get_db)):
    """Connect or create user"""
    try:
        # Get or create user
        user = db.query(User).filter(User.address == user_address).first()
        
        if not user:
            user = User(
                address=user_address,
                total_bets=0,
                total_wagered=0,
                total_won=0,
                total_lost=0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[OK] New user created: {user_address}")
        else:
            user.last_seen = datetime.utcnow()
            db.commit()
        
        # Get or create active seed
        seed = db.query(Seed).filter(
            Seed.user_id == user.id,
            Seed.is_active == True
        ).first()
        
        if not seed:
            server_seed, server_seed_hash, client_seed = generate_new_seed_pair(user_address)
            
            seed = Seed(
                user_id=user.id,
                server_seed=server_seed,
                server_seed_hash=server_seed_hash,
                client_seed=client_seed,
                nonce=0,
                is_active=True
            )
            db.add(seed)
            db.commit()
            db.refresh(seed)
        
        return {
            "user": UserResponse.from_orm(user),
            "server_seed_hash": seed.server_seed_hash,
            "client_seed": seed.client_seed,
            "nonce": seed.nonce
        }
        
    except Exception as e:
        logger.error(f"Error connecting user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/deposit/create", response_model=CreateDepositResponse)
async def create_deposit_address(
    request: CreateDepositRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a unique deposit address for a bet"""
    try:
        # Get or create user
        user = db.query(User).filter(User.address == request.user_address).first()
        
        if not user:
            user = User(address=request.user_address)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate unique deposit address
        # For testnet, we'll use a simple derivation
        # In production, use HD wallet derivation
        import hashlib
        import time
        
        # Simple deterministic address generation (for demo)
        # In production, use proper HD wallet
        unique_string = f"{user.address}_{int(time.time())}_{request.multiplier}"
        address_hash = hashlib.sha256(unique_string.encode()).hexdigest()[:20]
        
        # For testnet, we'll actually use the house address for simplicity
        # In production, generate proper child addresses from HD wallet
        deposit_address_str = config.HOUSE_ADDRESS  # Simplified for demo
        
        # Check if this address already has an active deposit for this user
        existing_deposit = db.query(DepositAddress).filter(
            DepositAddress.address == deposit_address_str,
            DepositAddress.user_id == user.id,
            DepositAddress.is_active == True,
            DepositAddress.is_used == False
        ).first()
        
        if existing_deposit:
            # Return the existing active deposit
            deposit_addr = existing_deposit
        else:
            # Delete all previous deposits with the same address
            # (since we're reusing the house address for testnet demo)
            db.query(DepositAddress).filter(
                DepositAddress.address == deposit_address_str
            ).delete()
            db.commit()
            
            # Create deposit address record
            deposit_addr = DepositAddress(
                user_id=user.id,
                address=deposit_address_str,
                is_active=True,
                is_used=False,
                expected_multiplier=request.multiplier,
                expected_amount_min=config.MIN_BET_SATOSHIS,
                expected_amount_max=config.MAX_BET_SATOSHIS,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            db.add(deposit_addr)
            db.commit()
            db.refresh(deposit_addr)
        
        # Setup webhook for this address
        detector = TransactionDetector(db)
        background_tasks.add_task(detector.setup_webhook, deposit_address_str)
        
        return CreateDepositResponse(
            deposit_address=deposit_address_str,
            multiplier=request.multiplier,
            min_amount=config.MIN_BET_SATOSHIS,
            max_amount=config.MAX_BET_SATOSHIS,
            expires_at=deposit_addr.expires_at
        )
        
    except Exception as e:
        logger.error(f"Error creating deposit address: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tx/submit")
async def submit_transaction(
    request: SubmitTxRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """User submits a transaction ID for verification"""
    try:
        detector = TransactionDetector(db)
        
        # Verify transaction
        tx = await detector.verify_user_submitted_tx(
            txid=request.txid,
            expected_address=request.deposit_address
        )
        
        if not tx:
            raise HTTPException(status_code=400, detail="Transaction not found or invalid")
        
        # Process transaction into bet
        processor = BetProcessor(db)
        bet = processor.process_detected_transaction(tx)
        
        if not bet:
            raise HTTPException(status_code=400, detail="Failed to process transaction")
        
        return {
            "success": True,
            "transaction_id": tx.txid,
            "bet_id": bet.id,
            "status": bet.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bets/user/{user_address}")
async def get_user_bets(
    user_address: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get user's bet history"""
    try:
        user = db.query(User).filter(User.address == user_address).first()
        
        if not user:
            return {"bets": [], "total": 0}
        
        bets = db.query(Bet).filter(
            Bet.user_id == user.id
        ).order_by(
            Bet.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        total = db.query(Bet).filter(Bet.user_id == user.id).count()
        
        return {
            "bets": [BetResponse.from_orm(bet) for bet in bets],
            "total": total
        }
        
    except Exception as e:
        logger.error(f"Error getting user bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bet/{bet_id}")
async def get_bet(bet_id: int, db: Session = Depends(get_db)):
    """Get bet details"""
    try:
        bet = db.query(Bet).filter(Bet.id == bet_id).first()
        
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        return BetResponse.from_orm(bet)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bet/verify", response_model=VerificationResponse)
async def verify_bet(request: VerifyBetRequest, db: Session = Depends(get_db)):
    """Verify bet fairness"""
    try:
        bet = db.query(Bet).filter(Bet.id == request.bet_id).first()
        
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        if bet.roll_result is None:
            raise HTTPException(status_code=400, detail="Bet not yet rolled")
        
        seed = db.query(Seed).filter(Seed.id == bet.seed_id).first()
        
        if not seed:
            raise HTTPException(status_code=404, detail="Seed not found")
        
        # Generate verification data
        verification = ProvablyFair.generate_verification_data(
            server_seed=seed.server_seed,
            server_seed_hash=seed.server_seed_hash,
            client_seed=seed.client_seed,
            nonce=bet.nonce,
            roll=bet.roll_result
        )
        
        # Mark seed as revealed if first time
        if not seed.revealed_at:
            seed.revealed_at = datetime.utcnow()
            db.commit()
        
        return VerificationResponse(
            bet_id=bet.id,
            server_seed=seed.server_seed,
            server_seed_hash=seed.server_seed_hash,
            client_seed=seed.client_seed,
            nonce=bet.nonce,
            roll=bet.roll_result,
            is_valid=verification['overall_valid'],
            verification_data=verification
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying bet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bets/recent")
async def get_recent_bets(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent bets (public)"""
    try:
        bets = db.query(Bet).filter(
            Bet.roll_result.isnot(None)
        ).order_by(
            Bet.rolled_at.desc()
        ).limit(limit).all()
        
        return {
            "bets": [BetResponse.from_orm(bet) for bet in bets]
        }
        
    except Exception as e:
        logger.error(f"Error getting recent bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhook/tx")
async def webhook_transaction(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """BlockCypher webhook endpoint for transaction notifications"""
    try:
        webhook_data = await request.json()
        
        logger.info(f"[WEBHOOK] Received: {webhook_data.get('hash', 'unknown')[:16]}...")
        
        # Process webhook
        detector = TransactionDetector(db)
        tx = detector.process_webhook_data(webhook_data)
        
        if tx:
            # Process into bet
            processor = BetProcessor(db)
            background_tasks.add_task(processor.process_detected_transaction, tx)
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/admin/process-pending")
async def process_pending(db: Session = Depends(get_db)):
    """Admin endpoint to process pending bets"""
    try:
        processor = BetProcessor(db)
        processed = processor.process_pending_bets()
        
        return {
            "processed": processed,
            "message": f"Processed {processed} bet(s)"
        }
        
    except Exception as e:
        logger.error(f"Error processing pending bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/retry-payouts")
async def retry_payouts(db: Session = Depends(get_db)):
    """Admin endpoint to retry failed payouts"""
    try:
        payout_engine = PayoutEngine(db)
        retried = payout_engine.retry_failed_payouts()
        
        return {
            "retried": retried,
            "message": f"Retried {retried} payout(s)"
        }
        
    except Exception as e:
        logger.error(f"Error retrying payouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL.lower()
    )
