"""
Database models and connection management
MongoDB with Motor (async driver) for the dice game
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pydantic import BaseModel, Field
from bson import ObjectId
from loguru import logger

from .config import config

# Global database client and database
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


class PyObjectId(str):
    """Custom type for MongoDB ObjectId"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


# Pydantic Models for MongoDB Documents
class UserModel(BaseModel):
    """User accounts and wallet addresses"""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    address: str = Field(..., max_length=64)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Statistics
    total_bets: int = 0
    total_wagered: int = 0  # in satoshis
    total_won: int = 0
    total_lost: int = 0
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class SeedModel(BaseModel):
    """Server and client seeds for provably fair system"""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    
    # Server seed (hidden until reveal)
    server_seed: str = Field(..., max_length=128)
    server_seed_hash: str = Field(..., max_length=128)  # SHA256 hash shown to user
    
    # Client seed
    client_seed: str = Field(..., max_length=128)
    
    # Nonce counter
    nonce: int = 0
    
    # Status
    is_active: bool = True
    revealed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class BetModel(BaseModel):
    """Individual bet records"""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    seed_id: PyObjectId
    
    # Bet details
    bet_amount: int  # satoshis
    target_multiplier: float
    win_chance: float  # percentage
    
    # Result
    nonce: int
    roll_result: Optional[float] = None  # 0.00 - 99.99
    is_win: Optional[bool] = None
    payout_amount: Optional[int] = None  # satoshis
    profit: Optional[int] = None  # satoshis (can be negative)
    
    # Transaction tracking
    deposit_txid: Optional[str] = Field(None, max_length=64)
    deposit_address: Optional[str] = Field(None, max_length=64)
    payout_txid: Optional[str] = Field(None, max_length=64)
    
    # Status tracking
    status: str = "pending"  # pending, confirmed, rolled, paid, failed
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    rolled_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class TransactionModel(BaseModel):
    """Transaction detection and state tracking"""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    txid: str = Field(..., max_length=64)
    bet_id: Optional[PyObjectId] = None
    
    # Transaction details
    from_address: Optional[str] = Field(None, max_length=64)
    to_address: str = Field(..., max_length=64)
    amount: int  # satoshis
    fee: Optional[int] = None
    
    # Detection metadata
    detected_by: str  # websocket, manual, api
    detection_count: int = 1  # how many times we detected this
    
    # Blockchain status
    confirmations: int = 0
    block_height: Optional[int] = None
    block_hash: Optional[str] = Field(None, max_length=64)
    
    # State tracking
    is_processed: bool = False
    is_duplicate: bool = False
    
    # Timestamps
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # Raw data for debugging
    raw_data: Optional[str] = None  # JSON string
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class PayoutModel(BaseModel):
    """Payout records and tracking"""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    bet_id: PyObjectId
    
    # Payout details
    amount: int  # satoshis
    to_address: str = Field(..., max_length=64)
    txid: Optional[str] = Field(None, max_length=64)
    
    # Status
    status: str = "pending"  # pending, broadcast, confirmed, failed
    error_message: Optional[str] = None
    
    # Fee tracking
    network_fee: Optional[int] = None
    
    # Retry logic
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    broadcast_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class DepositAddressModel(BaseModel):
    """Generated deposit addresses for users"""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    
    # Address details
    address: str = Field(..., max_length=64)
    derivation_path: Optional[str] = Field(None, max_length=50)  # For HD wallets
    
    # Status
    is_active: bool = True
    is_used: bool = False
    
    # Expected bet parameters (optional)
    expected_multiplier: Optional[float] = None
    expected_amount_min: Optional[int] = None
    expected_amount_max: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


# Database connection functions
async def connect_db():
    """Connect to MongoDB"""
    global _client, _database
    
    try:
        _client = AsyncIOMotorClient(config.MONGODB_URL)
        _database = _client[config.MONGODB_DB_NAME]
        
        # Test connection
        await _client.admin.command('ping')
        logger.info(f"[OK] Connected to MongoDB: {config.MONGODB_DB_NAME}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to connect to MongoDB: {e}")
        raise


async def disconnect_db():
    """Disconnect from MongoDB"""
    global _client
    
    if _client:
        _client.close()
        logger.info("[OK] Disconnected from MongoDB")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _database


# Collection accessors
def get_users_collection() -> AsyncIOMotorCollection:
    """Get users collection"""
    return get_database()["users"]


def get_seeds_collection() -> AsyncIOMotorCollection:
    """Get seeds collection"""
    return get_database()["seeds"]


def get_bets_collection() -> AsyncIOMotorCollection:
    """Get bets collection"""
    return get_database()["bets"]


def get_transactions_collection() -> AsyncIOMotorCollection:
    """Get transactions collection"""
    return get_database()["transactions"]


def get_payouts_collection() -> AsyncIOMotorCollection:
    """Get payouts collection"""
    return get_database()["payouts"]


def get_deposit_addresses_collection() -> AsyncIOMotorCollection:
    """Get deposit addresses collection"""
    return get_database()["deposit_addresses"]


async def create_indexes():
    """Create database indexes for optimal query performance"""
    db = get_database()
    
    # Users indexes
    await db.users.create_index("address", unique=True)
    await db.users.create_index([("created_at", -1)])
    
    # Seeds indexes
    await db.seeds.create_index([("user_id", 1), ("is_active", -1)])
    await db.seeds.create_index([("created_at", -1)])
    
    # Bets indexes
    await db.bets.create_index([("user_id", 1), ("created_at", -1)])
    await db.bets.create_index("status")
    await db.bets.create_index("deposit_txid")
    await db.bets.create_index([("created_at", -1)])
    
    # Transactions indexes
    await db.transactions.create_index("txid", unique=True)
    await db.transactions.create_index("to_address")
    await db.transactions.create_index("is_processed")
    await db.transactions.create_index("detected_by")
    await db.transactions.create_index([("detected_at", -1)])
    
    # Payouts indexes
    await db.payouts.create_index("txid", unique=True, sparse=True)
    await db.payouts.create_index("status")
    await db.payouts.create_index("to_address")
    await db.payouts.create_index([("created_at", -1)])
    
    # Deposit addresses indexes
    await db.deposit_addresses.create_index("address", unique=True)
    await db.deposit_addresses.create_index([("user_id", 1), ("is_active", -1)])
    await db.deposit_addresses.create_index("is_active")
    
    logger.info("[OK] Database indexes created")


# Initialize database (async version)
async def init_db():
    """Initialize database connection and indexes"""
    await connect_db()
    logger.info("[OK] Database initialized successfully")


# Drop database (use with caution!)
async def drop_db():
    """Drop entire database (use with caution!)"""
    db = get_database()
    await db.client.drop_database(config.MONGODB_DB_NAME)
    logger.warning(f"[WARNING] Database {config.MONGODB_DB_NAME} dropped")
