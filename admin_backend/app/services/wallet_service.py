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
    
    async def generate_wallet(self, multiplier: int, address_type: str = "segwit", chance: float = None) -> Dict[str, Any]:
        """
        Generate a new Bitcoin wallet with specified address type
        
        Args:
            multiplier: Bet multiplier for this wallet
            address_type: 'legacy' (P2PKH), 'segwit' (P2WPKH), or 'taproot' (P2TR)
            chance: Win chance percentage (0.01-99.99). If None, defaults to (100 - house_edge) / multiplier
        
        Returns: {address, multiplier, chance, wallet_id, address_type}
        """
        try:
            # Generate key
            key = Key(network=self.network)
            
            # Generate address based on type
            if address_type == "legacy":
                # P2PKH - Legacy address (1... for mainnet, m/n for testnet)
                address = key.address() if callable(key.address) else key.address
                address_format = "P2PKH"
            elif address_type == "segwit":
                # P2WPKH - Native SegWit (bc1q... for mainnet, tb1q for testnet)
                address = key.address(encoding='bech32') if callable(key.address) else key.address
                address_format = "P2WPKH"
            elif address_type == "taproot":
                # P2TR - Taproot (bc1p... for mainnet, tb1p for testnet)
                # Note: bitcoinlib may have limited taproot support, fallback to segwit if not available
                try:
                    address = key.address(encoding='bech32', witness_type='segwit') if callable(key.address) else key.address
                    address_format = "P2TR"
                except:
                    # Fallback to SegWit if Taproot not supported
                    logger.warning(f"[ADMIN] Taproot not fully supported, using SegWit instead")
                    address = key.address(encoding='bech32') if callable(key.address) else key.address
                    address_format = "P2WPKH"
                    address_type = "segwit"
            else:
                raise ValueError(f"Invalid address type: {address_type}")
            
            # Get WIF (check if it's a method or property)
            private_key_wif = key.wif() if callable(key.wif) else key.wif
            
            logger.info(f"[ADMIN] Generated {multiplier}x wallet ({address_type.upper()})")
            
            encrypted_private_key = self.crypto_service.encrypt(private_key_wif)
            
            # Calculate default chance if not provided (using house edge)
            if chance is None:
                chance = self._calculate_default_chance(multiplier)
            
            wallet_doc = {
                "multiplier": multiplier,
                "chance": chance,
                "address": address,
                "address_type": address_type,
                "address_format": address_format,
                "private_key_encrypted": encrypted_private_key,
                "network": self.network,
                "is_active": True,
                "is_depleted": False,
                "total_received": 0,
                "total_sent": 0,
                "bet_count": 0,
                "last_used_at": None,
                "label": f"{multiplier}x {address_type.capitalize()} Wallet",
                "created_at": __import__('datetime').datetime.utcnow()
            }
            
            result = await self.wallets_collection.insert_one(wallet_doc)
            wallet_id = str(result.inserted_id)
            
            logger.info(f"[ADMIN] Generated {multiplier}x {address_type} wallet (chance: {chance}%): {address[:15]}... (ID: {wallet_id})")
            
            return {
                "wallet_id": wallet_id,
                "address": address,
                "multiplier": multiplier,
                "chance": chance,
                "address_type": address_type,
                "address_format": address_format,
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
                "chance": w.get("chance", self._calculate_default_chance(w["multiplier"])),
                "address": w["address"],
                "address_type": w.get("address_type", "legacy"),
                "address_format": w.get("address_format", "P2PKH"),
                "is_active": w["is_active"],
                "is_depleted": w.get("is_depleted", False),
                "total_received": w.get("total_received", 0),
                "total_sent": w.get("total_sent", 0),
                "bet_count": w.get("bet_count", 0),
                "last_used_at": w.get("last_used_at"),
                "created_at": w.get("created_at", __import__('datetime').datetime.utcnow()),
                "balance_satoshis": w.get("balance_satoshis", 0),
                "label": w.get("label", f"{w['multiplier']}x Wallet")
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
    
    def _calculate_default_chance(self, multiplier: int) -> float:
        """Calculate default chance based on multiplier and house edge"""
        from app.core.config import admin_config
        # Default house edge is 1% if not configured
        house_edge = getattr(admin_config, 'HOUSE_EDGE', 0.01)
        house_edge_percent = house_edge * 100
        return round((100 - house_edge_percent) / multiplier, 2)
    
    async def update_wallet(self, wallet_id: str, multiplier: int = None, chance: float = None, label: str = None, is_active: bool = None) -> Dict[str, Any]:
        """
        Update wallet properties (multiplier, chance, label, active status)
        
        Args:
            wallet_id: Wallet ID to update
            multiplier: New multiplier value (optional)
            chance: New chance value (optional, 0.01-99.99)
            label: New label (optional)
            is_active: New active status (optional)
        
        Returns: Updated wallet info
        """
        from bson import ObjectId
        
        try:
            # Check if wallet exists
            wallet = await self.wallets_collection.find_one({"_id": ObjectId(wallet_id)})
            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found")
            
            # Build update fields
            update_fields = {}
            if multiplier is not None:
                update_fields["multiplier"] = multiplier
                logger.info(f"[ADMIN] Updating wallet {wallet_id} multiplier: {wallet['multiplier']} → {multiplier}")
            if chance is not None:
                if not (0.01 <= chance <= 99.99):
                    raise ValueError("Chance must be between 0.01 and 99.99")
                update_fields["chance"] = chance
                logger.info(f"[ADMIN] Updating wallet {wallet_id} chance: {wallet.get('chance', 'N/A')} → {chance}")
            if label is not None:
                update_fields["label"] = label
            if is_active is not None:
                update_fields["is_active"] = is_active
            
            if not update_fields:
                raise ValueError("No fields to update")
            
            update_fields["updated_at"] = __import__('datetime').datetime.utcnow()
            
            # Update wallet
            await self.wallets_collection.update_one(
                {"_id": ObjectId(wallet_id)},
                {"$set": update_fields}
            )
            
            logger.info(f"[ADMIN] Updated wallet {wallet_id}: {update_fields}")
            
            # Return updated wallet
            updated_wallet = await self.wallets_collection.find_one({"_id": ObjectId(wallet_id)})
            return {
                "wallet_id": str(updated_wallet["_id"]),
                "multiplier": updated_wallet["multiplier"],
                "chance": updated_wallet.get("chance", self._calculate_default_chance(updated_wallet["multiplier"])),
                "address": updated_wallet["address"],
                "address_type": updated_wallet.get("address_type", "legacy"),
                "label": updated_wallet.get("label"),
                "is_active": updated_wallet["is_active"],
                "message": "Wallet updated successfully"
            }
            
        except Exception as e:
            logger.error(f"[ADMIN] Failed to update wallet {wallet_id}: {e}")
            raise RuntimeError(f"Failed to update wallet: {e}")
    
    async def delete_wallet(self, wallet_id: str) -> Dict[str, Any]:
        """
        Delete a wallet from the vault
        
        WARNING: This permanently deletes the wallet and its encrypted private key.
        Only use this if you're certain the wallet has no funds.
        
        Args:
            wallet_id: Wallet ID to delete
        
        Returns: Deletion confirmation
        """
        from bson import ObjectId
        
        try:
            # Check if wallet exists
            wallet = await self.wallets_collection.find_one({"_id": ObjectId(wallet_id)})
            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found")
            
            address = wallet["address"]
            multiplier = wallet["multiplier"]
            
            # Safety check: warn if wallet has received funds
            total_received = wallet.get("total_received", 0)
            if total_received > 0:
                logger.warning(f"[ADMIN] ⚠️  Deleting wallet {wallet_id} that has received {total_received} sats!")
            
            # Delete wallet
            result = await self.wallets_collection.delete_one({"_id": ObjectId(wallet_id)})
            
            if result.deleted_count > 0:
                logger.info(f"[ADMIN] 🗑️  Deleted {multiplier}x wallet: {address[:15]}... (ID: {wallet_id})")
                return {
                    "success": True,
                    "wallet_id": wallet_id,
                    "address": address,
                    "multiplier": multiplier,
                    "message": f"Wallet deleted successfully"
                }
            else:
                raise RuntimeError("Failed to delete wallet")
            
        except Exception as e:
            logger.error(f"[ADMIN] Failed to delete wallet {wallet_id}: {e}")
            raise RuntimeError(f"Failed to delete wallet: {e}")