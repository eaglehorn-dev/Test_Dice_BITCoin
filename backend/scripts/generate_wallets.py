#!/usr/bin/env python3
"""
Admin Script: Generate Encrypted Wallet Vault
==============================================

This script generates Bitcoin wallets for different multipliers,
encrypts their private keys, and stores them in MongoDB.

Usage:
    python scripts/generate_wallets.py

Security:
- Requires MASTER_ENCRYPTION_KEY in .env file
- Private keys are encrypted before storage
- Never logs or displays decrypted keys

Default Multipliers: 2x, 3x, 5x, 10x, 100x
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import config
from app.services.wallet_service import WalletService
from app.services.crypto_service import generate_encryption_key


async def generate_master_key():
    """Generate a new master encryption key"""
    print("\n" + "="*60)
    print("GENERATE NEW MASTER ENCRYPTION KEY")
    print("="*60)
    print("\n⚠️  IMPORTANT: Save this key in your .env file!")
    print("Add this line to backend/.env:\n")
    
    key = generate_encryption_key()
    print(f"MASTER_ENCRYPTION_KEY={key}\n")
    
    print("="*60)
    print("Keep this key secret and NEVER commit it to git!")
    print("="*60 + "\n")


async def generate_wallets():
    """Generate wallets for standard multipliers"""
    
    if not config.MASTER_ENCRYPTION_KEY:
        print("\n❌ ERROR: MASTER_ENCRYPTION_KEY not found in .env")
        print("\nRun this script with '--generate-key' to create one:\n")
        print("    python scripts/generate_wallets.py --generate-key\n")
        return
    
    print("\n" + "="*60)
    print("WALLET VAULT GENERATOR")
    print("="*60)
    print(f"\nNetwork: {config.NETWORK}")
    print(f"Database: {config.MONGODB_DB_NAME}")
    print(f"Encryption: Fernet (AES-256)")
    print("\n" + "="*60 + "\n")
    
    try:
        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.MONGODB_DB_NAME]
        
        await client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {config.MONGODB_DB_NAME}")
        
        wallet_service = WalletService()
        
        multipliers = [2, 3, 5, 10, 100]
        
        print(f"Generating {len(multipliers)} wallets...\n")
        
        for multiplier in multipliers:
            existing = await wallet_service.get_wallet_for_multiplier(multiplier)
            
            if existing:
                print(f"⏭️  {multiplier}x wallet already exists: {existing['address']}")
                continue
            
            wallet = await wallet_service.create_wallet(
                multiplier=multiplier,
                network=config.NETWORK
            )
            
            print(f"✅ {multiplier}x → {wallet['address']}")
        
        print("\n" + "="*60)
        print("WALLET SUMMARY")
        print("="*60 + "\n")
        
        all_wallets = await wallet_service.get_active_wallets()
        
        for wallet in sorted(all_wallets, key=lambda w: w['multiplier']):
            print(f"{wallet['multiplier']:3}x  │  {wallet['address']}  │  {wallet['label']}")
        
        print("\n" + "="*60)
        print(f"✅ Total active wallets: {len(all_wallets)}")
        print("="*60 + "\n")
        
        print("🔒 Private keys are encrypted and stored securely in MongoDB")
        print("🎮 Your game is ready for multi-multiplier betting!\n")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"\n❌ Failed to generate wallets: {e}\n")
        sys.exit(1)


async def list_wallets():
    """List all existing wallets"""
    print("\n" + "="*60)
    print("EXISTING WALLETS")
    print("="*60 + "\n")
    
    try:
        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.MONGODB_DB_NAME]
        
        await client.admin.command('ping')
        
        wallet_service = WalletService()
        all_wallets = await wallet_service.get_active_wallets()
        
        if not all_wallets:
            print("No wallets found. Run without --list to generate wallets.\n")
            client.close()
            return
        
        print(f"{'Mult':<6} {'Address':<45} {'Status':<10} {'Balance':<12} {'Bets':<8}")
        print("-" * 90)
        
        for wallet in sorted(all_wallets, key=lambda w: w['multiplier']):
            status = "Active" if wallet['is_active'] else "Inactive"
            if wallet.get('is_depleted'):
                status = "Depleted"
            
            print(
                f"{wallet['multiplier']:3}x    "
                f"{wallet['address']:<45} "
                f"{status:<10} "
                f"{wallet.get('balance_satoshis', 0):>10} sat "
                f"{wallet.get('bet_count', 0):>6}"
            )
        
        print("\n" + "="*60)
        print(f"Total: {len(all_wallets)} wallets")
        print("="*60 + "\n")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"\n❌ Failed to list wallets: {e}\n")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--generate-key":
            asyncio.run(generate_master_key())
        elif sys.argv[1] == "--list":
            asyncio.run(list_wallets())
        elif sys.argv[1] == "--help":
            print("\nWallet Vault Generator")
            print("======================\n")
            print("Usage:")
            print("  python scripts/generate_wallets.py              # Generate wallets")
            print("  python scripts/generate_wallets.py --generate-key  # Generate encryption key")
            print("  python scripts/generate_wallets.py --list         # List existing wallets")
            print("  python scripts/generate_wallets.py --help         # Show this help\n")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        asyncio.run(generate_wallets())


if __name__ == "__main__":
    main()
