"""
Fix: Add network field to existing wallets
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_wallets():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["dice_test"]
    
    print("=" * 60)
    print("FIXING WALLET NETWORK FIELDS")
    print("=" * 60)
    
    # Find wallets without network field
    wallets_without_network = await db.wallets.count_documents({"network": {"$exists": False}})
    print(f"\nWallets without 'network' field: {wallets_without_network}")
    
    if wallets_without_network > 0:
        # Update all wallets to have network = "testnet"
        result = await db.wallets.update_many(
            {"network": {"$exists": False}},
            {"$set": {"network": "testnet"}}
        )
        print(f"\n[OK] Updated {result.modified_count} wallets with network='testnet'")
    else:
        print("\n[OK] All wallets already have network field")
    
    # Verify
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    wallets = await db.wallets.find({}).to_list(length=None)
    for wallet in wallets:
        print(f"\n[OK] {wallet.get('multiplier', 'N/A')}x - {wallet.get('address', 'N/A')[:20]}...")
        print(f"   Network: {wallet.get('network', 'MISSING!')}")
        print(f"   Active: {wallet.get('is_active', False)}")
    
    print("\n" + "=" * 60)
    print("FIX COMPLETE!")
    print("=" * 60)
    print("\nNow restart the main backend to see the wallets!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_wallets())
