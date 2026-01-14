"""
Wallet Service - Encrypted Wallet Vault Management
Handles dynamic wallet creation, encryption, and multiplier-based lookup
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from loguru import logger
from bitcoinlib.wallets import Wallet
from bitcoinlib.keys import Key

from app.core.config import config
from app.core.exceptions import DiceGameException, DatabaseException
from app.repository.wallet_repository import WalletRepository
from app.services.crypto_service import CryptoService


class WalletService:
    """
    Manages the encrypted wallet vault
    
    Security:
    - Private keys NEVER stored unencrypted
    - Decryption only in memory during transaction signing
    - No logging of sensitive data
    """
    
    def __init__(self):
        self.wallet_repo = WalletRepository()
        self.crypto_service = CryptoService()
    
    async def create_wallet(
        self,
        multiplier: int,
        label: Optional[str] = None,
        network: str = None
    ) -> Dict[str, Any]:
        """
        Generate a new Bitcoin wallet, encrypt it, and store in vault
        
        Args:
            multiplier: Payout multiplier (e.g., 2, 3, 5, 10, 100)
            label: Human-readable label
            network: Bitcoin network (mainnet/testnet)
            
        Returns:
            Wallet document (with encrypted private key)
            
        Security:
        - Private key encrypted before storage
        - Original key deleted from memory immediately
        """
        try:
            network = network or config.NETWORK
            
            logger.info(f"[VAULT] Generating new {multiplier}x wallet for {network}")
            
            key = Key(network=network)
            address = key.address()
            private_key_wif = key.wif()
            
            encrypted_key = self.crypto_service.encrypt_private_key(private_key_wif)
            
            del private_key_wif
            
            wallet_data = {
                "multiplier": multiplier,
                "address": address,
                "private_key_encrypted": encrypted_key,
                "network": network,
                "address_type": "P2WPKH" if network == "mainnet" else "P2WPKH",
                "is_active": True,
                "is_depleted": False,
                "total_received": 0,
                "total_sent": 0,
                "bet_count": 0,
                "balance_satoshis": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "label": label or f"{multiplier}x Multiplier Wallet"
            }
            
            wallet_id = await self.wallet_repo.create(wallet_data)
            wallet_data["_id"] = ObjectId(wallet_id)
            
            logger.info(f"[VAULT] ✅ Created {multiplier}x wallet: {address}")
            
            return wallet_data
            
        except Exception as e:
            logger.error(f"[VAULT] Failed to create wallet: {e}")
            raise DiceGameException(f"Wallet creation failed: {e}")
    
    async def get_wallet_for_multiplier(self, multiplier: int) -> Optional[Dict[str, Any]]:
        """
        Get an active wallet for a specific multiplier
        
        Args:
            multiplier: Desired payout multiplier
            
        Returns:
            Wallet document (public data only - private key still encrypted)
        """
        try:
            wallet = await self.wallet_repo.find_by_multiplier(multiplier, is_active=True)
            
            if not wallet:
                logger.warning(f"[VAULT] No active wallet found for {multiplier}x")
                return None
            
            return wallet
            
        except Exception as e:
            logger.error(f"[VAULT] Error getting wallet for multiplier {multiplier}: {e}")
            return None
    
    async def get_wallet_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Find wallet by Bitcoin address
        
        Args:
            address: Bitcoin address to look up
            
        Returns:
            Wallet document or None
        """
        try:
            return await self.wallet_repo.find_by_address(address)
        except Exception as e:
            logger.error(f"[VAULT] Error finding wallet by address: {e}")
            return None
    
    async def get_available_multipliers(self) -> List[int]:
        """
        Get list of all available multipliers
        
        Returns:
            Sorted list of multipliers (e.g., [2, 3, 5, 10, 100])
        """
        try:
            multipliers = await self.wallet_repo.get_all_multipliers(is_active=True)
            return multipliers
        except Exception as e:
            logger.error(f"[VAULT] Error getting multipliers: {e}")
            return []
    
    async def get_active_wallets(self) -> List[Dict[str, Any]]:
        """Get all active wallets (sorted by multiplier)"""
        try:
            return await self.wallet_repo.find_active_wallets(network=config.NETWORK)
        except Exception as e:
            logger.error(f"[VAULT] Error getting active wallets: {e}")
            return []
    
    def decrypt_private_key(self, wallet: Dict[str, Any]) -> str:
        """
        Decrypt wallet private key for transaction signing
        
        Args:
            wallet: Wallet document with encrypted key
            
        Returns:
            Decrypted WIF private key
            
        Security:
        - Use immediately and discard
        - NEVER log or persist the result
        - Call only when signing transactions
        """
        try:
            encrypted_key = wallet.get("private_key_encrypted")
            if not encrypted_key:
                raise DiceGameException("Wallet has no encrypted private key")
            
            return self.crypto_service.decrypt_private_key(encrypted_key)
            
        except Exception as e:
            logger.error(f"[VAULT] Decryption failed for wallet {wallet.get('address', 'unknown')}")
            raise DiceGameException("Failed to decrypt wallet private key")
    
    async def update_wallet_balance(self, wallet_id: str, balance_satoshis: int) -> bool:
        """Update wallet balance after checking blockchain"""
        try:
            return await self.wallet_repo.update_balance(wallet_id, balance_satoshis)
        except Exception as e:
            logger.error(f"[VAULT] Error updating balance: {e}")
            return False
    
    async def record_transaction(
        self,
        wallet_id: str,
        received: int = 0,
        sent: int = 0
    ) -> bool:
        """
        Record a transaction in wallet statistics
        
        Args:
            wallet_id: Wallet ID
            received: Satoshis received (for deposits)
            sent: Satoshis sent (for payouts)
        """
        try:
            bet_count = 1 if received > 0 else 0
            return await self.wallet_repo.increment_stats(
                wallet_id=wallet_id,
                received=received,
                sent=sent,
                bet_count=bet_count
            )
        except Exception as e:
            logger.error(f"[VAULT] Error recording transaction: {e}")
            return False
    
    async def mark_wallet_depleted(self, wallet_id: str, is_depleted: bool = True) -> bool:
        """Mark wallet as depleted (insufficient funds for payouts)"""
        try:
            logger.warning(f"[VAULT] Marking wallet {wallet_id} as {'depleted' if is_depleted else 'active'}")
            return await self.wallet_repo.mark_depleted(wallet_id, is_depleted)
        except Exception as e:
            logger.error(f"[VAULT] Error marking wallet depleted: {e}")
            return False
    
    async def deactivate_wallet(self, wallet_id: str) -> bool:
        """Deactivate a wallet (no longer available for new bets)"""
        try:
            result = await self.wallet_repo.update(wallet_id, {"is_active": False})
            logger.info(f"[VAULT] Wallet {wallet_id} deactivated")
            return result
        except Exception as e:
            logger.error(f"[VAULT] Error deactivating wallet: {e}")
            return False
