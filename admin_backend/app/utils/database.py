"""
MongoDB Database Connection (Shared with Main Backend)
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from loguru import logger
from app.core.config import admin_config

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

async def connect_db():
    """Connect to MongoDB"""
    global client, db
    try:
        client = AsyncIOMotorClient(admin_config.MONGODB_URL)
        db = client[admin_config.MONGODB_DB_NAME]
        await client.admin.command('ping')
        logger.info(f"[ADMIN] Connected to MongoDB: {admin_config.MONGODB_DB_NAME}")
    except Exception as e:
        logger.error(f"[ADMIN] MongoDB connection failed: {e}")
        raise

async def disconnect_db():
    """Disconnect from MongoDB"""
    global client
    if client:
        client.close()
        logger.info("[ADMIN] Disconnected from MongoDB")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db

def get_wallets_collection():
    """Get wallets collection"""
    return db["wallets"]

def get_bets_collection():
    """Get bets collection"""
    return db["bets"]

def get_payouts_collection():
    """Get payouts collection"""
    return db["payouts"]
