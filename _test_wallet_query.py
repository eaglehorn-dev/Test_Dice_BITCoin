"""
Temporary script to check wallets in MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_wallets():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["dice_test"]
    
    print("=" * 60)
    print("CHECKING WALLETS IN dice_test DATABASE")
    print("=" * 60)
    
    # Count wallets
    wallet_count = await db.wallets.count_documents({})
    print(f"\nTotal wallets in collection: {wallet_count}")
    
    if wallet_count > 0:
        print("\n" + "=" * 60)
        print("WALLET DETAILS:")
        print("=" * 60)
        
        wallets = await db.wallets.find({}).to_list(length=None)
        for wallet in wallets:
            print(f"\n[OK] Wallet ID: {wallet['_id']}")
            print(f"   Multiplier: {wallet.get('multiplier', 'N/A')}x")
            print(f"   Address: {wallet.get('address', 'N/A')}")
            print(f"   Network: {wallet.get('network', 'N/A')}")
            print(f"   Is Active: {wallet.get('is_active', False)}")
            print(f"   Is Depleted: {wallet.get('is_depleted', False)}")
            print(f"   Label: {wallet.get('label', 'N/A')}")
    else:
        print("\n[WARNING] NO WALLETS FOUND IN DATABASE!")
        print("\nTo generate wallets:")
        print("1. Go to: http://localhost:3001")
        print("2. Scroll to 'Wallet Vault' section")
        print("3. Generate wallets for 2x, 3x, 5x, 10x, 100x")
    
    print("\n" + "=" * 60)
    print("CHECKING INDEXES:")
    print("=" * 60)
    
    indexes = await db.wallets.index_information()
    for index_name, index_info in indexes.items():
        print(f"\n[INDEX] {index_name}")
        print(f"   Keys: {index_info.get('key', [])}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_wallets())
