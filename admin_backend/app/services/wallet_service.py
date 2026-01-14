"""
Wallet Management Service
Generate, store, and manage Bitcoin wallets
"""
from typing import Dict, Any, List
from bitcoinlib.keys import Key
from loguru import logger
from app.core.config import admin_config
from app.utils.database import get_wallets_collection
from app.services.crypto_service import CryptoService

class WalletService:
    """Manages Bitcoin wallet vault"""
    
    def __init__(self):
        self.wallets_collection = get_wallets_collection()
        self.crypto_service = CryptoService()
        self.network = 'bitcoin' if admin_config.NETWORK == 'mainnet' else 'testnet'
    
    async def generate_wallet(self, multiplier: int) -> Dict[str, Any]:
        """
        Generate a new Bitcoin wallet and encrypt its private key
        Returns: {address, multiplier, wallet_id}
        """
        try:
            key = Key(network=self.network)
            # Get address (check if it's a method or property)
            address = key.address() if callable(key.address) else key.address
            # Get WIF (check if it's a method or property)
            private_key_wif = key.wif() if callable(key.wif) else key.wif
            
            logger.info(f"[ADMIN] Generated {multiplier}x wallet")
            
            encrypted_private_key = self.crypto_service.encrypt(private_key_wif)
            
            wallet_doc = {
                "multiplier": multiplier,
                "address": address,
                "private_key_encrypted": encrypted_private_key,
                "network": self.network,  # ✅ Add network field
                "is_active": True,
                "is_depleted": False,
                "total_received": 0,
                "total_sent": 0,
                "bet_count": 0,
                "last_used_at": None,
                "label": f"{multiplier}x Wallet",  # ✅ Add label field
                "created_at": __import__('datetime').datetime.utcnow()
            }
            
            result = await self.wallets_collection.insert_one(wallet_doc)
            wallet_id = str(result.inserted_id)
            
            logger.info(f"[ADMIN] Generated {multiplier}x wallet: {address[:10]}... (ID: {wallet_id})")
            
            return {
                "wallet_id": wallet_id,
                "address": address,
                "multiplier": multiplier,
                "is_active": True
            }
        
        except Exception as e:
            logger.error(f"[ADMIN] Failed to generate wallet: {e}")
            raise RuntimeError(f"Wallet generation failed: {e}")
    
    async def get_all_wallets(self) -> List[Dict[str, Any]]:
        """Get all wallets (without private keys)"""
        try:
            wallets = await self.wallets_collection.find({}).to_list(length=None)
            
            return [{
                "wallet_id": str(w["_id"]),
                "multiplier": w["multiplier"],
                "address": w["address"],
                "is_active": w["is_active"],
                "is_depleted": w.get("is_depleted", False),
                "total_received": w.get("total_received", 0),
                "total_sent": w.get("total_sent", 0),
                "bet_count": w.get("bet_count", 0),
                "last_used_at": w.get("last_used_at"),
                "created_at": w.get("created_at", __import__('datetime').datetime.utcnow()),
                "balance_satoshis": w.get("balance_satoshis", 0)
            } for w in wallets]
        except Exception as e:
            logger.error(f"[ADMIN] Failed to get wallets: {e}")
            return []
    
    async def get_wallet_by_id(self, wallet_id: str) -> Dict[str, Any]:
        """Get wallet by ID (without private key)"""
        from bson import ObjectId
        wallet = await self.wallets_collection.find_one({"_id": ObjectId(wallet_id)})
        
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")
        
        return {
            "wallet_id": str(wallet["_id"]),
            "multiplier": wallet["multiplier"],
            "address": wallet["address"],
            "is_active": wallet["is_active"],
            "is_depleted": wallet.get("is_depleted", False),
            "total_received": wallet.get("total_received", 0),
            "total_sent": wallet.get("total_sent", 0),
            "bet_count": wallet.get("bet_count", 0),
            "encrypted_key_present": bool(wallet.get("private_key_encrypted"))
        }
    
    async def decrypt_wallet_key(self, wallet_id: str) -> str:
        """
        Decrypt private key for a wallet
        WARNING: Only call this when absolutely necessary (e.g., for withdrawals)
        """
        from bson import ObjectId
        wallet = await self.wallets_collection.find_one({"_id": ObjectId(wallet_id)})
        
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")
        
        encrypted_key = wallet.get("private_key_encrypted")
        if not encrypted_key:
            raise ValueError("Wallet has no encrypted private key")
        
        logger.warning(f"[ADMIN] Decrypting private key for wallet {wallet_id} - {wallet['address'][:10]}...")
        decrypted_key = self.crypto_service.decrypt(encrypted_key)
        
        return decrypted_key
    
    async def update_wallet_status(self, wallet_id: str, is_active: bool = None, is_depleted: bool = None):
        """Update wallet active/depleted status"""
        from bson import ObjectId
        update_fields = {}
        if is_active is not None:
            update_fields["is_active"] = is_active
        if is_depleted is not None:
            update_fields["is_depleted"] = is_depleted
        
        await self.wallets_collection.update_one(
            {"_id": ObjectId(wallet_id)},
            {"$set": update_fields}
        )
        
        logger.info(f"[ADMIN] Updated wallet {wallet_id} status: {update_fields}")
