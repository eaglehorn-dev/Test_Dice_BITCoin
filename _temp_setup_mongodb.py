"""
TEMPORARY MongoDB Setup Script
Run this ONCE to initialize databases and collections
DO NOT include in project - this is for initial setup only
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB Configuration
MONGODB_URL = "mongodb://localhost:27017"
PROD_DB_NAME = "dice_prod"
TEST_DB_NAME = "dice_test"

async def setup_database(db_name: str):
    """Setup a database with all required collections and indexes"""
    print(f"\n{'='*60}")
    print(f"Setting up database: {db_name}")
    print(f"{'='*60}")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[db_name]
    
    # ============================================================
    # 1. WALLETS COLLECTION (Encrypted Vault)
    # ============================================================
    print("\n[1/6] Creating 'wallets' collection...")
    wallets = db["wallets"]
    
    # Drop existing indexes if any
    try:
        await wallets.drop_indexes()
    except:
        pass
    
    # Create indexes
    await wallets.create_index("address", unique=True)
    await wallets.create_index("multiplier")
    await wallets.create_index([("is_active", 1), ("network", 1)])
    await wallets.create_index("created_at")
    
    print("   ✓ Indexes created:")
    print("     - address (unique)")
    print("     - multiplier")
    print("     - is_active + network")
    print("     - created_at")
    
    # ============================================================
    # 2. BETS COLLECTION
    # ============================================================
    print("\n[2/6] Creating 'bets' collection...")
    bets = db["bets"]
    
    try:
        await bets.drop_indexes()
    except:
        pass
    
    # Create indexes
    await bets.create_index("tx_hash", unique=True)
    await bets.create_index("target_address")  # Which vault wallet
    await bets.create_index("multiplier")  # For filtering by multiplier
    await bets.create_index("user_address")
    await bets.create_index("status")
    await bets.create_index("created_at")
    await bets.create_index([("is_win", 1), ("created_at", -1)])
    await bets.create_index([("target_address", 1), ("created_at", -1)])
    
    print("   ✓ Indexes created:")
    print("     - tx_hash (unique)")
    print("     - target_address (vault wallet)")
    print("     - multiplier")
    print("     - user_address")
    print("     - status")
    print("     - created_at")
    print("     - is_win + created_at")
    print("     - target_address + created_at")
    
    # ============================================================
    # 3. TRANSACTIONS COLLECTION
    # ============================================================
    print("\n[3/6] Creating 'transactions' collection...")
    transactions = db["transactions"]
    
    try:
        await transactions.drop_indexes()
    except:
        pass
    
    await transactions.create_index("txid", unique=True)
    await transactions.create_index("to_address")
    await transactions.create_index("from_address")
    await transactions.create_index("detected_at")
    await transactions.create_index("is_processed")
    
    print("   ✓ Indexes created:")
    print("     - txid (unique)")
    print("     - to_address")
    print("     - from_address")
    print("     - detected_at")
    print("     - is_processed")
    
    # ============================================================
    # 4. PAYOUTS COLLECTION
    # ============================================================
    print("\n[4/6] Creating 'payouts' collection...")
    payouts = db["payouts"]
    
    try:
        await payouts.drop_indexes()
    except:
        pass
    
    await payouts.create_index("txid", unique=True)
    await payouts.create_index("bet_id")
    await payouts.create_index("status")
    await payouts.create_index("created_at")
    await payouts.create_index([("wallet_id", 1), ("created_at", -1)])
    
    print("   ✓ Indexes created:")
    print("     - txid (unique)")
    print("     - bet_id")
    print("     - status")
    print("     - created_at")
    print("     - wallet_id + created_at")
    
    # ============================================================
    # 5. USERS COLLECTION
    # ============================================================
    print("\n[5/6] Creating 'users' collection...")
    users = db["users"]
    
    try:
        await users.drop_indexes()
    except:
        pass
    
    await users.create_index("address", unique=True)
    await users.create_index("created_at")
    await users.create_index("last_bet_at")
    
    print("   ✓ Indexes created:")
    print("     - address (unique)")
    print("     - created_at")
    print("     - last_bet_at")
    
    # ============================================================
    # 6. DEPOSIT_ADDRESSES COLLECTION (if needed)
    # ============================================================
    print("\n[6/6] Creating 'deposit_addresses' collection...")
    deposit_addresses = db["deposit_addresses"]
    
    try:
        await deposit_addresses.drop_indexes()
    except:
        pass
    
    await deposit_addresses.create_index("address", unique=True)
    await deposit_addresses.create_index("user_id")
    await deposit_addresses.create_index("created_at")
    
    print("   ✓ Indexes created:")
    print("     - address (unique)")
    print("     - user_id")
    print("     - created_at")
    
    # ============================================================
    # Summary
    # ============================================================
    collections = await db.list_collection_names()
    print(f"\n{'='*60}")
    print(f"✅ Database '{db_name}' setup complete!")
    print(f"{'='*60}")
    print(f"Collections created: {len(collections)}")
    for coll in sorted(collections):
        print(f"  - {coll}")
    
    client.close()
    
    return True

async def verify_setup():
    """Verify the setup"""
    print(f"\n{'='*60}")
    print("VERIFICATION")
    print(f"{'='*60}")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    
    # Check production database
    print(f"\n[PROD] Database: {PROD_DB_NAME}")
    prod_db = client[PROD_DB_NAME]
    prod_collections = await prod_db.list_collection_names()
    print(f"   Collections: {len(prod_collections)}")
    for coll in sorted(prod_collections):
        count = await prod_db[coll].count_documents({})
        print(f"     - {coll}: {count} documents")
    
    # Check test database
    print(f"\n[TEST] Database: {TEST_DB_NAME}")
    test_db = client[TEST_DB_NAME]
    test_collections = await test_db.list_collection_names()
    print(f"   Collections: {len(test_collections)}")
    for coll in sorted(test_collections):
        count = await test_db[coll].count_documents({})
        print(f"     - {coll}: {count} documents")
    
    client.close()

async def main():
    """Main setup function"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        Bitcoin Dice Game - MongoDB Setup Script         ║
║                                                          ║
║  This script will create databases and collections      ║
║  for both PRODUCTION and TEST environments              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print(f"MongoDB URL: {MONGODB_URL}")
    print(f"Production DB: {PROD_DB_NAME}")
    print(f"Test DB: {TEST_DB_NAME}")
    
    # Confirm
    print("\nThis will create/reset the following databases:")
    print(f"  1. {PROD_DB_NAME}")
    print(f"  2. {TEST_DB_NAME}")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Setup cancelled.")
        return
    
    try:
        # Setup production database
        await setup_database(PROD_DB_NAME)
        
        # Setup test database
        await setup_database(TEST_DB_NAME)
        
        # Verify
        await verify_setup()
        
        print(f"\n{'='*60}")
        print("✅ MongoDB setup completed successfully!")
        print(f"{'='*60}")
        print("\nNext steps:")
        print("1. Run 'backend/generate_wallets.py' to create vault wallets")
        print("2. Start the backend server")
        print("3. Delete this temporary script: _temp_setup_mongodb.py")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 Starting MongoDB setup...")
    asyncio.run(main())
