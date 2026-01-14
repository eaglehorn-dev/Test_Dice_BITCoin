"""
Verify that the generated addresses are valid testnet addresses
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def verify_addresses():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["dice_test"]
    
    print("=" * 70)
    print("BITCOIN ADDRESS FORMAT GUIDE")
    print("=" * 70)
    
    print("\n[MAINNET ADDRESSES]")
    print("   - Legacy (P2PKH):    Start with '1'  (e.g., 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa)")
    print("   - Script (P2SH):     Start with '3'  (e.g., 3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy)")
    print("   - SegWit (P2WPKH):   Start with 'bc1' (e.g., bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4)")
    
    print("\n[TESTNET ADDRESSES]")
    print("   - Legacy (P2PKH):    Start with 'm' or 'n'  (e.g., mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn)")
    print("   - Script (P2SH):     Start with '2'  (e.g., 2MzQwSSnBHWHqSAqtTVQ6v47XtaisrJa1Vc)")
    print("   - SegWit (P2WPKH):   Start with 'tb1' (e.g., tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx)")
    
    print("\n" + "=" * 70)
    print("YOUR GENERATED WALLET ADDRESSES (from MongoDB)")
    print("=" * 70)
    
    wallets = await db.wallets.find({}).to_list(length=None)
    
    for wallet in wallets:
        address = wallet.get('address', 'N/A')
        multiplier = wallet.get('multiplier', 'N/A')
        
        # Determine address type
        address_type = "UNKNOWN"
        is_testnet = False
        
        if address.startswith('1'):
            address_type = "MAINNET Legacy (P2PKH)"
        elif address.startswith('3'):
            address_type = "MAINNET Script (P2SH)"
        elif address.startswith('bc1'):
            address_type = "MAINNET SegWit (P2WPKH)"
        elif address[0] in ['m', 'n']:
            address_type = "TESTNET Legacy (P2PKH)"
            is_testnet = True
        elif address.startswith('2'):
            address_type = "TESTNET Script (P2SH)"
            is_testnet = True
        elif address.startswith('tb1'):
            address_type = "TESTNET SegWit (P2WPKH)"
            is_testnet = True
        
        status = "[OK] VALID TESTNET" if is_testnet else "[ERROR] NOT TESTNET!"
        
        print(f"\n{multiplier}x Wallet: {address}")
        print(f"   Type: {address_type}")
        print(f"   Status: {status}")
    
    print("\n" + "=" * 70)
    print("VERDICT:")
    print("=" * 70)
    
    testnet_count = sum(1 for w in wallets if w.get('address', '')[0] in ['m', 'n', '2'] or w.get('address', '').startswith('tb1'))
    mainnet_count = len(wallets) - testnet_count
    
    if mainnet_count > 0:
        print(f"\n[ERROR] Found {mainnet_count} MAINNET address(es)!")
        print("        These should NOT be used for testing!")
    
    if testnet_count > 0:
        print(f"\n[OK] Found {testnet_count} TESTNET address(es)")
        print("     These are CORRECT for testing!")
    
    print("\n" + "=" * 70)
    print("EXPLANATION:")
    print("=" * 70)
    print("""
Addresses starting with 'm' or 'n' are VALID TESTNET addresses!

These are "Legacy" P2PKH testnet addresses, which are perfectly fine to use.
You can receive testnet Bitcoin at these addresses from:
- https://testnet-faucet.mempool.co/
- https://coinfaucet.eu/en/btc-testnet/

Modern wallets also use 'tb1' addresses (SegWit), but 'm'/'n' addresses 
work just as well on testnet!
""")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(verify_addresses())
