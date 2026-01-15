"""
TEMPORARY Script to Clean Test Database
This will delete all data from dice_test database
Run this script to reset the test database

Usage:
    python _temp_clean_test_db.py          # Interactive mode (asks for confirmation)
    python _temp_clean_test_db.py --yes     # Auto-confirm (non-interactive)
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

# MongoDB Configuration
MONGODB_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "dice_test"

async def clean_test_database():
    """Clean all collections in test database"""
    print(f"\n{'='*60}")
    print(f"Cleaning Test Database: {TEST_DB_NAME}")
    print(f"{'='*60}\n")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[TEST_DB_NAME]
    
    # Collections to clean
    collections_to_clean = [
        "bets",
        "payouts",
        "transactions",
        "users",
        "deposit_addresses",
        "seeds",
        "wallets",  # Be careful - this will delete all wallet vault data!
        "counters"  # Reset bet counter
    ]
    
    print("WARNING: This will delete ALL data from the following collections:")
    for col in collections_to_clean:
        print(f"   - {col}")
    
    print("\nWARNING: This action cannot be undone!")
    
    # Check for --yes flag for non-interactive mode
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
    
    if not auto_confirm:
        try:
            response = input("\nType 'YES' to confirm: ")
            if response != "YES":
                print("Operation cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled (no input available)")
            return
    else:
        print("\n[Auto-confirm] Proceeding with database cleanup...")
    
    print("\nCleaning collections...")
    
    for collection_name in collections_to_clean:
        try:
            collection = db[collection_name]
            count = await collection.count_documents({})
            await collection.delete_many({})
            print(f"   [OK] Deleted {count} document(s) from '{collection_name}'")
        except Exception as e:
            print(f"   [ERROR] Error cleaning '{collection_name}': {e}")
    
    # Reset bet counter
    try:
        counters_col = db["counters"]
        await counters_col.delete_one({"_id": "bet_number"})
        print(f"   [OK] Reset bet counter")
    except Exception as e:
        print(f"   [ERROR] Error resetting counter: {e}")
    
    print(f"\n[SUCCESS] Test database cleaned successfully!")
    print(f"   Database: {TEST_DB_NAME}")
    print(f"   Collections cleaned: {len(collections_to_clean)}")
    
    client.close()

if __name__ == "__main__":
    try:
        asyncio.run(clean_test_database())
    except KeyboardInterrupt:
        print("\n\n[ERROR] Operation cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
