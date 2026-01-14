"""
Transaction Service - Bitcoin transaction detection and processing
"""
import httpx
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from app.core.config import config
from app.core.exceptions import BlockchainException
from app.models.database import get_transactions_collection, get_deposit_addresses_collection
from app.repository.transaction_repository import TransactionRepository


class TransactionService:
    """
    Transaction detection and processing service
    Uses Mempool.space REST API for transaction detection and verification
    """
    
    def __init__(self):
        self.network = config.NETWORK
        self.tx_repo = TransactionRepository()
    
    async def check_mempool_space_api(self, address: str) -> List[Dict[str, Any]]:
        """
        Check Mempool.space API for transactions
        
        Args:
            address: Bitcoin address
            
        Returns:
            List of transaction dictionaries
        """
        try:
            url = f"{config.MEMPOOL_SPACE_API}/address/{address}/txs"
            
            async with httpx.AsyncClient(timeout=float(config.API_REQUEST_TIMEOUT)) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Mempool.space API returned {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error checking Mempool.space API: {e}")
            raise BlockchainException(f"Failed to check transactions: {str(e)}")
    
    async def get_transaction_details(self, txid: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from Mempool.space
        
        Args:
            txid: Transaction ID
            
        Returns:
            Transaction details dictionary or None
        """
        try:
            url = f"{config.MEMPOOL_SPACE_API}/tx/{txid}"
            
            async with httpx.AsyncClient(timeout=float(config.API_REQUEST_TIMEOUT)) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Transaction {txid} not found in Mempool.space")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting transaction details: {e}")
            return None
    
    async def verify_user_submitted_tx(
        self,
        txid: str,
        expected_address: str,
        expected_amount: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Verify a user-submitted transaction
        
        Args:
            txid: Transaction ID
            expected_address: Expected destination address
            expected_amount: Expected amount (optional)
            
        Returns:
            Transaction document or None
        """
        try:
            # Check if already in database
            existing_tx = await self.tx_repo.get_by_txid(txid)
            if existing_tx:
                logger.info(f"Transaction {txid[:16]}... already in database")
                return existing_tx
            
            # Fetch from Mempool.space
            tx_data = await self.get_transaction_details(txid)
            if not tx_data:
                return None
            
            # Process the transaction
            return await self._process_mempool_tx(txid, expected_address, source="manual")
            
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return None
    
    async def verify_transaction_for_vault(self, txid: str) -> Optional[Dict[str, Any]]:
        """
        Verify a transaction against all vault wallets
        
        Args:
            txid: Transaction ID
            
        Returns:
            Transaction document with target_address and multiplier, or None
        """
        try:
            from app.services.wallet_service import WalletService
            
            # Get all active vault wallets
            wallet_service = WalletService()
            active_wallets = await wallet_service.get_active_wallets()
            
            if not active_wallets:
                logger.warning("[TX] No active vault wallets to verify against")
                return None
            
            # Fetch transaction data
            tx_data = await self.get_transaction_details(txid)
            if not tx_data:
                return None
            
            # Check which vault wallet received the transaction
            vout = tx_data.get('vout', [])
            
            for wallet in active_wallets:
                vault_address = wallet["address"]
                amount = 0
                
                for output in vout:
                    if output.get('scriptpubkey_address') == vault_address:
                        amount += output.get('value', 0)
                
                if amount > 0:
                    # Found the target vault wallet!
                    tx_doc = await self._process_mempool_tx(txid, vault_address, source="manual")
                    if tx_doc:
                        # Enrich with vault wallet info
                        tx_doc["target_address"] = vault_address
                        tx_doc["multiplier"] = wallet["multiplier"]
                        logger.info(f"[TX] Transaction matches {wallet['multiplier']}x vault wallet")
                    return tx_doc
            
            logger.warning(f"[TX] Transaction {txid[:16]}... not sent to any vault wallet")
            return None
            
        except Exception as e:
            logger.error(f"Error verifying transaction for vault: {e}")
            return None
    
    async def _process_mempool_tx(
        self,
        txid: str,
        address: str,
        source: str = "websocket"
    ) -> Optional[Dict[str, Any]]:
        """
        Process a transaction from Mempool.space
        
        Args:
            txid: Transaction ID
            address: Expected destination address
            source: Detection source (websocket, manual, api)
            
        Returns:
            Transaction document or None
        """
        try:
            tx_col = get_transactions_collection()
            
            # Check if already exists
            existing = await tx_col.find_one({"txid": txid})
            if existing:
                logger.info(f"[TX] Transaction {txid[:16]}... already in database")
                return existing
            
            # Fetch transaction data
            tx_data = await self.get_transaction_details(txid)
            if not tx_data:
                return None
            
            # Find output to our address
            vout = tx_data.get('vout', [])
            amount = 0
            
            for output in vout:
                if output.get('scriptpubkey_address') == address:
                    amount += output.get('value', 0)
            
            if amount == 0:
                logger.warning(f"[TX] No output to {address} in tx {txid}")
                return None
            
            # Extract input addresses (from)
            from_address = None
            vin = tx_data.get('vin', [])
            if vin and len(vin) > 0:
                from_address = vin[0].get('prevout', {}).get('scriptpubkey_address')
            
            # Block info
            status = tx_data.get('status', {})
            confirmations = status.get('confirmed', False)
            block_height = status.get('block_height')
            block_hash = status.get('block_hash')
            
            # Create transaction document
            tx_doc = {
                "txid": txid,
                "from_address": from_address,
                "to_address": address,
                "amount": amount,
                "fee": tx_data.get('fee', 0),
                "detected_by": source,
                "detection_count": 1,
                "confirmations": 1 if confirmations else 0,
                "block_height": block_height,
                "block_hash": block_hash,
                "is_processed": False,
                "is_duplicate": False,
                "detected_at": datetime.utcnow(),
                "confirmed_at": datetime.utcnow() if confirmations else None,
                "raw_data": json.dumps(tx_data)
            }
            
            # Insert into database
            result = await tx_col.insert_one(tx_doc)
            tx_doc["_id"] = result.inserted_id
            
            amount_btc = amount / 100000000
            logger.info(f"✅ [TX] Saved {txid[:16]}... ({amount_btc:.8f} BTC to {address[:10]}...)")
            
            return tx_doc
            
        except Exception as e:
            logger.error(f"Error processing Mempool tx: {e}")
            raise BlockchainException(f"Failed to process transaction: {str(e)}")
