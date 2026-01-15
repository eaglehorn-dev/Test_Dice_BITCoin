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
        
        # Ensure collections exist
        await ensure_collections_exist()
        
    except Exception as e:
        logger.error(f"[ADMIN] MongoDB connection failed: {e}")
        raise

async def ensure_collections_exist():
    """Ensure all required collections exist"""
    try:
        existing_collections = await db.list_collection_names()
        required_collections = ["wallets", "bets", "payouts", "transactions", "users", "deposit_addresses", "server_seeds"]
        
        for collection_name in required_collections:
            if collection_name not in existing_collections:
                await db.create_collection(collection_name)
                logger.info(f"[ADMIN] Created collection: {collection_name}")
            else:
                logger.debug(f"[ADMIN] Collection exists: {collection_name}")
        
        # Create indexes for wallets collection
        wallets = db["wallets"]
        await wallets.create_index("address", unique=True)
        await wallets.create_index("multiplier")
        await wallets.create_index("is_active")
        
        # Create indexes for bets collection
        bets = db["bets"]
        await bets.create_index("target_address")
        await bets.create_index("multiplier")
        await bets.create_index("deposit_txid", unique=True, sparse=True)
        await bets.create_index("created_at")
        
        # Create indexes for server_seeds collection (one seed per day)
        server_seeds = db["server_seeds"]
        await server_seeds.create_index("seed_date", unique=True)
        await server_seeds.create_index("seed_date", -1)
        
        logger.success("[ADMIN] All collections and indexes initialized")
        
    except Exception as e:
        logger.warning(f"[ADMIN] Failed to ensure collections: {e}")

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

def get_server_seeds_collection():
    """Get server seeds collection"""
    return db["server_seeds"]
