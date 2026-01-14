"""
FastAPI Main Application
REST API for Bitcoin Dice Game - MongoDB Version
"""
import asyncio
import json
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timedelta
import sys
from bson import ObjectId

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger

from .config import config
from .database import (
    init_db, disconnect_db, get_database,
    get_users_collection, get_seeds_collection, get_bets_collection,
    get_transactions_collection, get_payouts_collection, get_deposit_addresses_collection,
    UserModel, SeedModel, BetModel, TransactionModel, PayoutModel, DepositAddressModel
)
from .provably_fair import ProvablyFair, generate_new_seed_pair
from .blockchain import TransactionDetector, TransactionMonitor
from .payout import PayoutEngine, BetProcessor

# Setup Loguru logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.LOG_LEVEL,
    colorize=True
)

if config.ENABLE_LOGGING:
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )

# Global transaction monitor
tx_monitor = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

manager = ConnectionManager()


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
    await init_db()
    logger.info("[OK] Database initialized")
    
    # Start transaction monitor (Mempool.space WebSocket mode)
    global tx_monitor
    tx_monitor = TransactionMonitor()
    asyncio.create_task(tx_monitor.start())
    logger.info("[OK] Transaction monitor started (MEMPOOL.SPACE MODE)")
    logger.info("[INFO] Using Mempool.space WebSocket for real-time transaction detection")
    logger.info(f"[INFO] Monitoring address: {config.HOUSE_ADDRESS}")
    
    yield
    
    # Shutdown
    logger.info("[SHUTDOWN] Shutting down Bitcoin Dice Game API")
    if tx_monitor:
        tx_monitor.stop()
    await disconnect_db()


# Create FastAPI app
app = FastAPI(
    title="Bitcoin Dice Game API",
    description="Provably Fair Bitcoin Dice Game with Multi-Layer Transaction Detection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow all origins for development/public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class UserResponse(BaseModel):
    id: str
    address: str
    total_bets: int
    total_wagered: int
    total_won: int
    total_lost: int
    created_at: datetime


class SeedResponse(BaseModel):
    id: str
    server_seed_hash: str
    client_seed: str
    nonce: int
    is_active: bool
    revealed: bool = False
    server_seed: Optional[str] = None


class BetResponse(BaseModel):
    id: str
    user_address: Optional[str] = None  # Sender's Bitcoin address
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
    bet_id: str


class VerificationResponse(BaseModel):
    bet_id: str
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


@app.get("/api/config/house-address")
async def get_house_address():
    """Get the house address for receiving bets"""
    return {
        "address": config.HOUSE_ADDRESS,
        "network": config.NETWORK,
        "min_bet": config.MIN_BET_SATOSHIS,
        "max_bet": config.MAX_BET_SATOSHIS
    }


@app.get("/api/stats")
async def get_stats():
    """Get global statistics"""
    try:
        users_col = get_users_collection()
        bets_col = get_bets_collection()
        
        total_users = await users_col.count_documents({})
        total_bets = await bets_col.count_documents({})
        
        # Calculate total wagered
        pipeline = [
            {"$match": {"bet_amount": {"$exists": True}}},
            {"$group": {"_id": None, "total": {"$sum": "$bet_amount"}}}
        ]
        wagered_result = await bets_col.aggregate(pipeline).to_list(1)
        total_wagered = wagered_result[0]["total"] if wagered_result else 0
        
        # Calculate win rate
        total_wins = await bets_col.count_documents({"is_win": True})
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


@app.websocket("/ws/bets")
async def websocket_bets(websocket: WebSocket):
    """WebSocket endpoint for real-time bet updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for client messages (ping/pong)
            data = await websocket.receive_text()
            # Echo back to confirm connection is alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.post("/api/user/connect")
async def connect_user(user_address: str):
    """Connect or create user"""
    try:
        users_col = get_users_collection()
        seeds_col = get_seeds_collection()
        
        # Get or create user
        user = await users_col.find_one({"address": user_address})
        
        if not user:
            user_data = {
                "address": user_address,
                "created_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "total_bets": 0,
                "total_wagered": 0,
                "total_won": 0,
                "total_lost": 0
            }
            result = await users_col.insert_one(user_data)
            user = await users_col.find_one({"_id": result.inserted_id})
            logger.info(f"[OK] New user created: {user_address}")
        else:
            await users_col.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_seen": datetime.utcnow()}}
            )
        
        # Get or create active seed
        seed = await seeds_col.find_one({
            "user_id": str(user["_id"]),
            "is_active": True
        })
        
        if not seed:
            server_seed, server_seed_hash, client_seed = generate_new_seed_pair(user_address)
            
            seed_data = {
                "user_id": str(user["_id"]),
                "server_seed": server_seed,
                "server_seed_hash": server_seed_hash,
                "client_seed": client_seed,
                "nonce": 0,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            result = await seeds_col.insert_one(seed_data)
            seed = await seeds_col.find_one({"_id": result.inserted_id})
        
        return {
            "user": {
                "id": str(user["_id"]),
                "address": user["address"],
                "total_bets": user["total_bets"],
                "total_wagered": user["total_wagered"],
                "total_won": user["total_won"],
                "total_lost": user["total_lost"],
                "created_at": user["created_at"]
            },
            "server_seed_hash": seed["server_seed_hash"],
            "client_seed": seed["client_seed"],
            "nonce": seed["nonce"]
        }
        
    except Exception as e:
        logger.error(f"Error connecting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/deposit/create", response_model=CreateDepositResponse)
async def create_deposit_address(
    request: CreateDepositRequest,
    background_tasks: BackgroundTasks
):
    """Create a unique deposit address for a bet"""
    try:
        users_col = get_users_collection()
        deposit_col = get_deposit_addresses_collection()
        
        # Get or create user
        user = await users_col.find_one({"address": request.user_address})
        
        if not user:
            user_data = {
                "address": request.user_address,
                "created_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "total_bets": 0,
                "total_wagered": 0,
                "total_won": 0,
                "total_lost": 0
            }
            result = await users_col.insert_one(user_data)
            user = await users_col.find_one({"_id": result.inserted_id})
        
        # For testnet, we'll use the house address for simplicity
        deposit_address_str = config.HOUSE_ADDRESS
        
        # Check if this address already has an active deposit for this user
        existing_deposit = await deposit_col.find_one({
            "address": deposit_address_str,
            "user_id": str(user["_id"]),
            "is_active": True,
            "is_used": False
        })
        
        if existing_deposit:
            deposit_addr = existing_deposit
        else:
            # Delete all previous deposits with the same address
            await deposit_col.delete_many({"address": deposit_address_str})
            
            # Create deposit address record
            deposit_data = {
                "user_id": str(user["_id"]),
                "address": deposit_address_str,
                "is_active": True,
                "is_used": False,
                "expected_multiplier": request.multiplier,
                "expected_amount_min": config.MIN_BET_SATOSHIS,
                "expected_amount_max": config.MAX_BET_SATOSHIS,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            }
            
            result = await deposit_col.insert_one(deposit_data)
            deposit_addr = await deposit_col.find_one({"_id": result.inserted_id})
        
        # Subscribe to this address via WebSocket
        if tx_monitor and tx_monitor.websocket_client:
            background_tasks.add_task(tx_monitor.subscribe_address, deposit_address_str)
        
        return CreateDepositResponse(
            deposit_address=deposit_address_str,
            multiplier=request.multiplier,
            min_amount=config.MIN_BET_SATOSHIS,
            max_amount=config.MAX_BET_SATOSHIS,
            expires_at=deposit_addr.get("expires_at")
        )
        
    except Exception as e:
        logger.error(f"Error creating deposit address: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tx/submit")
async def submit_transaction(
    request: SubmitTxRequest,
    background_tasks: BackgroundTasks
):
    """User submits a transaction ID for verification"""
    try:
        detector = TransactionDetector()
        
        # Verify transaction
        tx = await detector.verify_user_submitted_tx(
            txid=request.txid,
            expected_address=request.deposit_address
        )
        
        if not tx:
            raise HTTPException(status_code=400, detail="Transaction not found or invalid")
        
        # Process transaction into bet
        processor = BetProcessor()
        bet = await processor.process_detected_transaction(tx)
        
        if not bet:
            raise HTTPException(status_code=400, detail="Failed to process transaction")
        
        # Broadcast new bet via WebSocket if rolled
        if bet.get("roll_result") is not None:
            await manager.broadcast({
                "type": "new_bet",
                "bet": bet
            })
        
        return {
            "success": True,
            "transaction_id": tx["txid"],
            "bet_id": str(bet["_id"]),
            "status": bet["status"]
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
    offset: int = 0
):
    """Get user's bet history"""
    try:
        users_col = get_users_collection()
        bets_col = get_bets_collection()
        
        user = await users_col.find_one({"address": user_address})
        
        if not user:
            return {"bets": [], "total": 0}
        
        user_id_str = str(user["_id"])
        
        bets_cursor = bets_col.find({"user_id": user_id_str}).sort("created_at", -1).skip(offset).limit(limit)
        bets = await bets_cursor.to_list(length=limit)
        
        total = await bets_col.count_documents({"user_id": user_id_str})
        
        # Get user addresses for each bet
        for bet in bets:
            bet_user = await users_col.find_one({"_id": ObjectId(bet["user_id"])})
            bet["user_address"] = bet_user["address"] if bet_user else None
            bet["id"] = str(bet["_id"])
        
        return {
            "bets": bets,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"Error getting user bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bet/{bet_id}")
async def get_bet(bet_id: str):
    """Get bet details"""
    try:
        bets_col = get_bets_collection()
        users_col = get_users_collection()
        
        bet = await bets_col.find_one({"_id": ObjectId(bet_id)})
        
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        # Get user address
        user = await users_col.find_one({"_id": ObjectId(bet["user_id"])})
        bet["user_address"] = user["address"] if user else None
        bet["id"] = str(bet["_id"])
        
        return bet
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bet/verify", response_model=VerificationResponse)
async def verify_bet(request: VerifyBetRequest):
    """Verify bet fairness"""
    try:
        bets_col = get_bets_collection()
        seeds_col = get_seeds_collection()
        
        bet = await bets_col.find_one({"_id": ObjectId(request.bet_id)})
        
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        if bet.get("roll_result") is None:
            raise HTTPException(status_code=400, detail="Bet not yet rolled")
        
        seed = await seeds_col.find_one({"_id": ObjectId(bet["seed_id"])})
        
        if not seed:
            raise HTTPException(status_code=404, detail="Seed not found")
        
        # Generate verification data
        verification = ProvablyFair.generate_verification_data(
            server_seed=seed["server_seed"],
            server_seed_hash=seed["server_seed_hash"],
            client_seed=seed["client_seed"],
            nonce=bet["nonce"],
            roll=bet["roll_result"]
        )
        
        # Mark seed as revealed if first time
        if not seed.get("revealed_at"):
            await seeds_col.update_one(
                {"_id": seed["_id"]},
                {"$set": {"revealed_at": datetime.utcnow()}}
            )
        
        return VerificationResponse(
            bet_id=str(bet["_id"]),
            server_seed=seed["server_seed"],
            server_seed_hash=seed["server_seed_hash"],
            client_seed=seed["client_seed"],
            nonce=bet["nonce"],
            roll=bet["roll_result"],
            is_valid=verification['overall_valid'],
            verification_data=verification
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying bet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bets/recent")
async def get_recent_bets(limit: int = 20):
    """Get recent bets (public)"""
    try:
        bets_col = get_bets_collection()
        users_col = get_users_collection()
        
        bets_cursor = bets_col.find({"roll_result": {"$ne": None}}).sort("rolled_at", -1).limit(limit)
        bets = await bets_cursor.to_list(length=limit)
        
        # Get user addresses for each bet
        for bet in bets:
            user = await users_col.find_one({"_id": ObjectId(bet["user_id"])})
            bet["user_address"] = user["address"] if user else None
            bet["id"] = str(bet["_id"])
        
        return {
            "bets": bets
        }
        
    except Exception as e:
        logger.error(f"Error getting recent bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/process-pending")
async def process_pending():
    """Admin endpoint to process pending bets"""
    try:
        processor = BetProcessor()
        processed = await processor.process_pending_bets()
        
        return {
            "processed": processed,
            "message": f"Processed {processed} bet(s)"
        }
        
    except Exception as e:
        logger.error(f"Error processing pending bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/retry-payouts")
async def retry_payouts():
    """Admin endpoint to retry failed payouts"""
    try:
        payout_engine = PayoutEngine()
        retried = await payout_engine.retry_failed_payouts()
        
        return {
            "retried": retried,
            "message": f"Retried {retried} payout(s)"
        }
        
    except Exception as e:
        logger.error(f"Error retrying payouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/process-tx/{txid}")
async def manually_process_transaction(txid: str):
    """
    Manually process a transaction by TXID
    Useful for testing or re-processing transactions
    """
    try:
        logger.info(f"[MANUAL] Processing transaction: {txid}")
        
        # Verify and fetch transaction
        detector = TransactionDetector()
        tx = await detector.verify_user_submitted_tx(
            txid=txid,
            expected_address=config.HOUSE_ADDRESS
        )
        
        if not tx:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {txid} not found or doesn't pay to house address"
            )
        
        # Process into bet
        processor = BetProcessor()
        bet = await processor.process_detected_transaction(tx)
        
        if not bet:
            raise HTTPException(
                status_code=400,
                detail="Failed to create bet from transaction"
            )
        
        # Get user address
        users_col = get_users_collection()
        user = await users_col.find_one({"_id": ObjectId(bet["user_id"])})
        
        # Broadcast via WebSocket if rolled
        if bet["status"] in ['paid', 'pending_payout']:
            await manager.broadcast({
                "type": "new_bet",
                "bet": {
                    "id": str(bet["_id"]),
                    "amount": bet["bet_amount"],
                    "multiplier": bet["target_multiplier"],
                    "win_chance": bet["win_chance"],
                    "result": "win" if bet["is_win"] else "loss",
                    "payout": bet.get("payout_amount"),
                    "status": bet["status"],
                    "user_address": user["address"] if user else None,
                    "created_at": bet["created_at"].isoformat()
                }
            })
        
        result_text = "WIN" if bet.get("is_win") else "LOSS"
        logger.info(f"[MANUAL] Bet created: ID {bet['_id']}, Result: {result_text}")
        
        return {
            "success": True,
            "bet_id": str(bet["_id"]),
            "result": "win" if bet.get("is_win") else "loss",
            "amount": bet["bet_amount"],
            "payout": bet.get("payout_amount"),
            "status": bet["status"],
            "message": f"Transaction processed successfully - {result_text}!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MANUAL] Error processing transaction: {e}")
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
