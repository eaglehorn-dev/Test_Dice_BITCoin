"""
Database connection management for MongoDB
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from loguru import logger

from app.core.config import config

# Global database client and database
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


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


def get_wallets_collection() -> AsyncIOMotorCollection:
    """Get wallets collection (encrypted vault)"""
    return get_database()["wallets"]


def get_server_seeds_collection() -> AsyncIOMotorCollection:
    """Get server seeds collection (fixed server seeds)"""
    return get_database()["server_seeds"]


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
    await db.bets.create_index("bet_number", unique=True)  # Incremental bet number (1, 2, 3, ...)
    await db.bets.create_index([("user_id", 1), ("created_at", -1)])
    await db.bets.create_index("status")
    await db.bets.create_index("deposit_txid", unique=True, sparse=True)
    await db.bets.create_index("target_address")
    await db.bets.create_index("multiplier")
    await db.bets.create_index([("target_address", 1), ("multiplier", 1)])
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
    
    # Wallets indexes (Vault)
    await db.wallets.create_index("address", unique=True)
    await db.wallets.create_index("multiplier")
    await db.wallets.create_index([("is_active", -1), ("multiplier", 1)])
    await db.wallets.create_index("network")
    
    # Server Seeds indexes (One seed per day)
    await db.server_seeds.create_index("seed_date", unique=True)
    await db.server_seeds.create_index([("seed_date", -1)])
    
    logger.info("[OK] Database indexes created")


async def init_db():
    """Initialize database connection and indexes"""
    await connect_db()
    logger.info("[OK] Database initialized successfully")


async def drop_db():
    """Drop entire database (use with caution!)"""
    db = get_database()
    await db.client.drop_database(config.MONGODB_DB_NAME)
    logger.warning(f"[WARNING] Database {config.MONGODB_DB_NAME} dropped")
