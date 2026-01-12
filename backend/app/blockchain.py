"""
Multi-Layer Transaction Detection System
Handles BlockCypher testnet3 unreliability with multiple fallback layers
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import requests
import httpx
from blockcypher import get_address_details, get_transaction_details, subscribe_to_address_webhook
from sqlalchemy.orm import Session

from .config import config
from .database import Transaction, DepositAddress

logger = logging.getLogger(__name__)


class TransactionDetector:
    """
    Multi-layer transaction detection system
    
    Layers:
    1. BlockCypher Webhooks (primary)
    2. BlockCypher API Polling (backup)
    3. Public Explorer APIs (fallback)
    4. User-submitted TXIDs (final fallback)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.api_token = config.BLOCKCYPHER_API_TOKEN
        self.network = config.BLOCKCYPHER_NETWORK
        
    # =============================================================================
    # LAYER 1: BlockCypher Webhooks
    # =============================================================================
    
    def setup_webhook(self, address: str) -> Optional[str]:
        """
        Setup BlockCypher webhook for address monitoring
        
        Args:
            address: Bitcoin address to monitor
            
        Returns:
            Webhook ID or None if failed
        """
        if not config.WEBHOOK_CALLBACK_URL:
            logger.warning("Webhook callback URL not configured, skipping webhook setup")
            return None
        
        try:
            result = subscribe_to_address_webhook(
                address=address,
                callback_url=config.WEBHOOK_CALLBACK_URL,
                event='unconfirmed-tx',
                api_key=self.api_token,
                coin_symbol='btc-testnet'
            )
            
            webhook_id = result.get('id')
            logger.info(f"[OK] Webhook created for {address}: {webhook_id}")
            return webhook_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create webhook for {address}: {e}")
            return None
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> Optional[Transaction]:
        """
        Process incoming webhook data from BlockCypher
        
        Args:
            webhook_data: Raw webhook payload
            
        Returns:
            Transaction object or None
        """
        try:
            # Extract transaction data
            tx_hash = webhook_data.get('hash')
            
            if not tx_hash:
                logger.error("Webhook data missing transaction hash")
                return None
            
            # Get full transaction details
            tx_details = self._get_blockcypher_tx(tx_hash)
            
            if not tx_details:
                logger.error(f"Failed to fetch tx details for {tx_hash}")
                return None
            
            # Process and store transaction
            return self._process_transaction_data(tx_details, 'webhook')
            
        except Exception as e:
            logger.error(f"Error processing webhook data: {e}")
            return None
    
    # =============================================================================
    # LAYER 2: BlockCypher API Polling
    # =============================================================================
    
    def poll_address(self, address: str) -> List[Transaction]:
        """
        Poll BlockCypher API for transactions to an address
        
        Args:
            address: Bitcoin address to check
            
        Returns:
            List of new transactions
        """
        try:
            # Get address details from BlockCypher
            address_data = get_address_details(
                address,
                coin_symbol='btc-testnet',
                api_key=self.api_token,
                unspent_only=False
            )
            
            if not address_data:
                return []
            
            # Extract transactions
            txrefs = address_data.get('txrefs', []) + address_data.get('unconfirmed_txrefs', [])
            
            new_transactions = []
            
            for txref in txrefs:
                tx_hash = txref.get('tx_hash')
                
                # Check if we already have this transaction
                existing = self.db.query(Transaction).filter(
                    Transaction.txid == tx_hash
                ).first()
                
                if existing:
                    # Update confirmations if changed
                    confirmations = txref.get('confirmations', 0)
                    if confirmations != existing.confirmations:
                        existing.confirmations = confirmations
                        if confirmations >= config.CONFIRMATIONS_REQUIRED and not existing.confirmed_at:
                            existing.confirmed_at = datetime.utcnow()
                        self.db.commit()
                    continue
                
                # Fetch full transaction details
                tx_details = self._get_blockcypher_tx(tx_hash)
                
                if tx_details:
                    tx_obj = self._process_transaction_data(tx_details, 'polling')
                    if tx_obj:
                        new_transactions.append(tx_obj)
            
            return new_transactions
            
        except Exception as e:
            logger.error(f"Error polling address {address}: {e}")
            return []
    
    def poll_all_active_addresses(self) -> int:
        """
        Poll all active deposit addresses for new transactions
        
        Returns:
            Number of new transactions detected
        """
        try:
            # Get all active deposit addresses
            active_addresses = self.db.query(DepositAddress).filter(
                DepositAddress.is_active == True,
                DepositAddress.is_used == False
            ).all()
            
            total_new = 0
            
            for deposit_addr in active_addresses:
                new_txs = self.poll_address(deposit_addr.address)
                total_new += len(new_txs)
                
                if new_txs:
                    logger.info(f"[POLLING] Found {len(new_txs)} new tx(s) for {deposit_addr.address}")
            
            return total_new
            
        except Exception as e:
            logger.error(f"Error in poll_all_active_addresses: {e}")
            return 0
    
    # =============================================================================
    # LAYER 3: Public Explorer Fallback APIs
    # =============================================================================
    
    async def check_blockstream_api(self, address: str) -> List[Dict[str, Any]]:
        """
        Check Blockstream.info API for transactions
        
        Args:
            address: Bitcoin address
            
        Returns:
            List of transaction dictionaries
        """
        try:
            url = f"{config.BLOCKSTREAM_API}/address/{address}/txs"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Blockstream API returned {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error checking Blockstream API: {e}")
            return []
    
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Mempool.space API returned {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error checking Mempool.space API: {e}")
            return []
    
    async def fallback_api_check(self, address: str) -> List[Transaction]:
        """
        Check public APIs as fallback for BlockCypher
        
        Args:
            address: Bitcoin address to check
            
        Returns:
            List of new transactions
        """
        new_transactions = []
        
        try:
            # Try Blockstream first
            blockstream_txs = await self.check_blockstream_api(address)
            
            for tx_data in blockstream_txs:
                tx_hash = tx_data.get('txid')
                
                if not tx_hash:
                    continue
                
                # Check if already exists
                existing = self.db.query(Transaction).filter(
                    Transaction.txid == tx_hash
                ).first()
                
                if existing:
                    continue
                
                # Convert to our format and store
                tx_obj = self._process_fallback_tx(tx_data, address, 'blockstream')
                if tx_obj:
                    new_transactions.append(tx_obj)
            
            # If Blockstream didn't work, try Mempool.space
            if not blockstream_txs:
                mempool_txs = await self.check_mempool_space_api(address)
                
                for tx_data in mempool_txs:
                    tx_hash = tx_data.get('txid')
                    
                    if not tx_hash:
                        continue
                    
                    existing = self.db.query(Transaction).filter(
                        Transaction.txid == tx_hash
                    ).first()
                    
                    if existing:
                        continue
                    
                    tx_obj = self._process_fallback_tx(tx_data, address, 'mempool_space')
                    if tx_obj:
                        new_transactions.append(tx_obj)
            
            if new_transactions:
                logger.info(f"[FALLBACK] APIs found {len(new_transactions)} new tx(s)")
            
            return new_transactions
            
        except Exception as e:
            logger.error(f"Error in fallback API check: {e}")
            return []
    
    # =============================================================================
    # LAYER 4: User-Submitted TXID Verification
    # =============================================================================
    
    async def verify_user_submitted_tx(self, txid: str, expected_address: str, expected_amount: Optional[int] = None) -> Optional[Transaction]:
        """
        Verify and process a user-submitted transaction ID
        
        Args:
            txid: Transaction hash provided by user
            expected_address: Address that should receive the payment
            expected_amount: Expected amount (optional)
            
        Returns:
            Transaction object if valid, None otherwise
        """
        try:
            # Check if already exists
            existing = self.db.query(Transaction).filter(
                Transaction.txid == txid
            ).first()
            
            if existing:
                logger.info(f"Transaction {txid} already exists")
                return existing
            
            # Try BlockCypher first
            tx_details = self._get_blockcypher_tx(txid)
            
            if tx_details:
                # Verify it pays to expected address
                outputs = tx_details.get('outputs', [])
                found = False
                amount = 0
                
                for output in outputs:
                    if expected_address in output.get('addresses', []):
                        found = True
                        amount = output.get('value', 0)
                        break
                
                if not found:
                    logger.warning(f"TX {txid} does not pay to {expected_address} (BlockCypher)")
                    logger.info(f"Trying fallback APIs to verify tx {txid}")
                    
                    # Try fallback APIs before giving up
                    tx_obj = await self._fetch_tx_from_fallback(txid, expected_address)
                    if tx_obj:
                        logger.info(f"[OK] Transaction verified via fallback API")
                        return tx_obj
                    else:
                        logger.error(f"TX {txid} does not pay to {expected_address} (verified by multiple sources)")
                        return None
                
                if expected_amount and amount != expected_amount:
                    logger.warning(f"TX {txid} amount mismatch: expected {expected_amount}, got {amount}")
                    return None
                
                # Process and store
                return self._process_transaction_data(tx_details, 'user_submit')
            
            else:
                # BlockCypher couldn't fetch the tx at all - try fallback APIs
                logger.info(f"BlockCypher failed to fetch tx {txid}, trying fallback APIs")
                
                # Try to fetch from public API
                tx_obj = await self._fetch_tx_from_fallback(txid, expected_address)
                
                if tx_obj:
                    logger.info(f"[OK] Transaction verified via fallback API")
                    return tx_obj
                else:
                    logger.error(f"Could not verify user-submitted tx {txid} (not found in any API)")
                    return None
                    
        except Exception as e:
            logger.error(f"Error verifying user-submitted tx: {e}")
            return None
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _get_blockcypher_tx(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from BlockCypher
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction data or None
        """
        try:
            tx_data = get_transaction_details(
                tx_hash,
                coin_symbol='btc-testnet',
                api_key=self.api_token
            )
            return tx_data
            
        except Exception as e:
            logger.error(f"Error fetching tx {tx_hash} from BlockCypher: {e}")
            return None
    
    def _process_transaction_data(self, tx_data: Dict[str, Any], detected_by: str) -> Optional[Transaction]:
        """
        Process and store transaction data from BlockCypher
        
        Args:
            tx_data: Transaction data from BlockCypher
            detected_by: Detection method (webhook, polling, etc.)
            
        Returns:
            Transaction object or None
        """
        try:
            tx_hash = tx_data.get('hash')
            
            # Check for duplicate
            existing = self.db.query(Transaction).filter(
                Transaction.txid == tx_hash
            ).first()
            
            if existing:
                # Update detection count
                existing.detection_count += 1
                if detected_by not in existing.detected_by:
                    existing.detected_by += f",{detected_by}"
                self.db.commit()
                return existing
            
            # Extract data
            inputs = tx_data.get('inputs', [])
            outputs = tx_data.get('outputs', [])
            confirmations = tx_data.get('confirmations', 0)
            block_height = tx_data.get('block_height')
            block_hash = tx_data.get('block_hash')
            
            # Get sender address (from first input)
            from_address = None
            if inputs:
                from_address = inputs[0].get('addresses', [None])[0]
            
            # Find which of our deposit addresses received payment
            our_output = None
            for output in outputs:
                output_addresses = output.get('addresses', [])
                for addr in output_addresses:
                    deposit_addr = self.db.query(DepositAddress).filter(
                        DepositAddress.address == addr,
                        DepositAddress.is_active == True
                    ).first()
                    
                    if deposit_addr:
                        our_output = output
                        break
                
                if our_output:
                    break
            
            if not our_output:
                logger.warning(f"TX {tx_hash} does not pay to any of our deposit addresses")
                return None
            
            to_address = our_output.get('addresses', [None])[0]
            amount = our_output.get('value', 0)
            
            # Calculate fee
            total_input = sum(inp.get('output_value', 0) for inp in inputs)
            total_output = sum(out.get('value', 0) for out in outputs)
            fee = total_input - total_output
            
            # Create transaction record
            transaction = Transaction(
                txid=tx_hash,
                from_address=from_address,
                to_address=to_address,
                amount=amount,
                fee=fee if fee > 0 else None,
                detected_by=detected_by,
                detection_count=1,
                confirmations=confirmations,
                block_height=block_height,
                block_hash=block_hash,
                is_processed=False,
                is_duplicate=False,
                detected_at=datetime.utcnow(),
                confirmed_at=datetime.utcnow() if confirmations >= config.CONFIRMATIONS_REQUIRED else None,
                raw_data=json.dumps(tx_data)
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"[OK] New transaction detected: {tx_hash[:16]}... amount={amount} conf={confirmations}")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error processing transaction data: {e}")
            self.db.rollback()
            return None
    
    def _process_fallback_tx(self, tx_data: Dict[str, Any], address: str, source: str) -> Optional[Transaction]:
        """
        Process transaction data from fallback APIs
        
        Args:
            tx_data: Transaction data from fallback API
            address: Our address that received payment
            source: Source API (blockstream, mempool_space)
            
        Returns:
            Transaction object or None
        """
        try:
            tx_hash = tx_data.get('txid')
            
            # Check for duplicate
            existing = self.db.query(Transaction).filter(
                Transaction.txid == tx_hash
            ).first()
            
            if existing:
                existing.detection_count += 1
                self.db.commit()
                return existing
            
            # Extract data (format differs by API)
            status = tx_data.get('status', {})
            confirmations = status.get('block_height', 0)
            if confirmations > 0:
                # Calculate confirmations (approximation)
                confirmations = 1  # Simplified
            
            # Find output to our address
            vout = tx_data.get('vout', [])
            amount = 0
            from_address = None
            found_address = False
            
            for output in vout:
                if output.get('scriptpubkey_address') == address:
                    amount = output.get('value', 0)
                    found_address = True
                    break
            
            # Verify transaction pays to expected address
            if not found_address:
                logger.warning(f"TX {tx_hash} does not pay to {address} (fallback API)")
                return None
            
            # Verify amount is not zero
            if amount == 0:
                logger.warning(f"TX {tx_hash} has zero amount to {address}")
                return None
            
            # Get sender (from first input)
            vin = tx_data.get('vin', [])
            if vin:
                from_address = vin[0].get('prevout', {}).get('scriptpubkey_address')
            
            # Create transaction record
            transaction = Transaction(
                txid=tx_hash,
                from_address=from_address,
                to_address=address,
                amount=amount,
                detected_by=f'fallback_{source}',
                detection_count=1,
                confirmations=confirmations,
                is_processed=False,
                detected_at=datetime.utcnow(),
                raw_data=json.dumps(tx_data)
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"[OK] Fallback API ({source}) transaction: {tx_hash[:16]}... amount={amount}")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error processing fallback transaction: {e}")
            self.db.rollback()
            return None
    
    async def _fetch_tx_from_fallback(self, txid: str, expected_address: str) -> Optional[Transaction]:
        """Fetch and verify transaction from fallback APIs"""
        try:
            # Try Blockstream
            logger.info(f"[FALLBACK] Trying Blockstream API for tx {txid[:16]}...")
            url = f"{config.BLOCKSTREAM_API}/tx/{txid}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    logger.info(f"[FALLBACK] Blockstream found tx {txid[:16]}...")
                    tx_data = response.json()
                    result = self._process_fallback_tx(tx_data, expected_address, 'blockstream')
                    if result:
                        return result
                    logger.info(f"[FALLBACK] Blockstream tx validation failed, trying next API")
                else:
                    logger.info(f"[FALLBACK] Blockstream returned status {response.status_code}")
            
            # Try Mempool.space
            logger.info(f"[FALLBACK] Trying Mempool.space API for tx {txid[:16]}...")
            url = f"{config.MEMPOOL_SPACE_API}/tx/{txid}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    logger.info(f"[FALLBACK] Mempool.space found tx {txid[:16]}...")
                    tx_data = response.json()
                    result = self._process_fallback_tx(tx_data, expected_address, 'mempool_space')
                    if result:
                        return result
                    logger.info(f"[FALLBACK] Mempool.space tx validation failed")
                else:
                    logger.info(f"[FALLBACK] Mempool.space returned status {response.status_code}")
            
            logger.warning(f"[FALLBACK] All fallback APIs failed for tx {txid[:16]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching tx from fallback APIs: {e}")
            return None


# Background polling task
class TransactionMonitor:
    """Background service to continuously monitor for transactions"""
    
    def __init__(self):
        self.running = False
        self.poll_interval = config.POLLING_INTERVAL_SECONDS
    
    async def start(self):
        """Start the monitoring service"""
        self.running = True
        logger.info("[MONITOR] Transaction monitor started")
        
        while self.running:
            try:
                from .database import SessionLocal
                db = SessionLocal()
                
                detector = TransactionDetector(db)
                new_count = detector.poll_all_active_addresses()
                
                if new_count > 0:
                    logger.info(f"[MONITOR] Found {new_count} new transaction(s)")
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error in transaction monitor: {e}")
            
            # Wait before next poll
            await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop the monitoring service"""
        self.running = False
        logger.info("[SHUTDOWN] Transaction monitor stopped")
