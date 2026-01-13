"""
Transaction Detection System using Mempool.space API
Real-time monitoring via WebSocket and REST API
"""
import asyncio
import json
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
import httpx
import websockets
from sqlalchemy.orm import Session
from loguru import logger

from .config import config
from .database import Transaction, DepositAddress


class TransactionDetector:
    """
    Transaction detection system using Mempool.space API
    
    Uses Mempool.space REST API for transaction detection and verification
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.network = config.NETWORK
    
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
            return []
    
    async def get_transaction_details(self, txid: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from Mempool.space
        
        Args:
            txid: Transaction hash
            
        Returns:
            Transaction data or None
        """
        try:
            url = f"{config.MEMPOOL_SPACE_API}/tx/{txid}"
            
            async with httpx.AsyncClient(timeout=float(config.API_REQUEST_TIMEOUT)) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Mempool.space API returned {response.status_code} for tx {txid}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching transaction {txid}: {e}")
            return None
    
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
            
            # Get transaction details from Mempool.space
            tx_data = await self.get_transaction_details(txid)
            
            if not tx_data:
                logger.error(f"Could not fetch transaction {txid}")
                return None
            
            # Process and store
            return self._process_mempool_tx(tx_data, expected_address, 'user_submit')
                    
        except Exception as e:
            logger.error(f"Error verifying user-submitted tx: {e}")
            return None
    
    async def check_address_transactions(self, address: str) -> List[Transaction]:
        """
        Check Mempool.space API for new transactions to an address
        
        Args:
            address: Bitcoin address to check
            
        Returns:
            List of new transactions
        """
        new_transactions = []
        
        try:
            # Get transactions from Mempool.space
            mempool_txs = await self.check_mempool_space_api(address)
            
            for tx_data in mempool_txs:
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
                tx_obj = self._process_mempool_tx(tx_data, address, 'mempool_space')
                if tx_obj:
                    new_transactions.append(tx_obj)
            
            if new_transactions:
                logger.info(f"[MEMPOOL] Found {len(new_transactions)} new tx(s)")
            
            return new_transactions
            
        except Exception as e:
            logger.error(f"Error checking address transactions: {e}")
            return []
    
    def _process_mempool_tx(self, tx_data: Dict[str, Any], address: str, source: str) -> Optional[Transaction]:
        """
        Process transaction data from Mempool.space API
        
        Args:
            tx_data: Transaction data from Mempool.space
            address: Our address that received payment
            source: Source (mempool_space, user_submit, etc.)
            
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
            
            # Extract data
            status = tx_data.get('status', {})
            confirmations = 0
            block_height = None
            
            if status.get('confirmed'):
                confirmations = 1  # Simplified - would need current block height for accurate count
                block_height = status.get('block_height')
            
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
                logger.warning(f"TX {tx_hash} does not pay to {address}")
                return None
            
            # Verify amount is not zero
            if amount == 0:
                logger.warning(f"TX {tx_hash} has zero amount to {address}")
                return None
            
            # Get sender (from first input)
            vin = tx_data.get('vin', [])
            if vin:
                from_address = vin[0].get('prevout', {}).get('scriptpubkey_address')
            
            # Calculate fee
            fee = tx_data.get('fee', 0)
            
            # Create transaction record
            transaction = Transaction(
                txid=tx_hash,
                from_address=from_address,
                to_address=address,
                amount=amount,
                fee=fee if fee > 0 else None,
                detected_by=source,
                detection_count=1,
                confirmations=confirmations,
                block_height=block_height,
                is_processed=False,
                detected_at=datetime.utcnow(),
                raw_data=json.dumps(tx_data, default=str)
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"[OK] Transaction detected: {tx_hash[:16]}... amount={amount} conf={confirmations}")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error processing Mempool.space transaction: {e}")
            self.db.rollback()
            return None


# Mempool.space WebSocket client
class MempoolWebSocket:
    """
    WebSocket client for real-time transaction monitoring via Mempool.space
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.network = config.NETWORK
        self.websocket = None
        self.running = False
        self.subscribed_addresses: Set[str] = set()
        self.reconnect_delay = config.WS_RECONNECT_DELAY
        self.max_reconnect_delay = config.WS_MAX_RECONNECT_DELAY
        
        # WebSocket URL from config
        self.ws_url = config.MEMPOOL_WEBSOCKET_URL
    
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            logger.info(f"[WEBSOCKET] Connecting to {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=config.WS_PING_INTERVAL,
                ping_timeout=config.WS_PING_TIMEOUT,
                close_timeout=10
            )
            logger.info("[WEBSOCKET] Connected successfully to Mempool.space")
            self.reconnect_delay = 5  # Reset delay on successful connection
            return True
        except Exception as e:
            logger.error(f"[WEBSOCKET] Connection failed: {e}")
            return False
    
    async def subscribe_to_mempool(self):
        """Subscribe to mempool data"""
        if not self.websocket:
            logger.warning(f"[WEBSOCKET] Not connected, cannot subscribe to mempool")
            return False
        
        try:
            # Subscribe to mempool blocks and stats
            subscribe_msg = {
                "action": "want",
                "data": ["blocks", "mempool-blocks", "live-2h-chart", "stats"]
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"[WEBSOCKET] Subscribed to mempool data")
            return True
        except Exception as e:
            logger.error(f"[WEBSOCKET] Failed to subscribe to mempool: {e}")
            return False
    
    async def subscribe_address(self, address: str):
        """Track a specific address for transaction notifications"""
        if not self.websocket:
            logger.warning(f"[WEBSOCKET] Not connected, cannot track address")
            return False
        
        try:
            # Track specific address - this is the key!
            track_msg = {
                "track-address": address
            }
            
            await self.websocket.send(json.dumps(track_msg))
            self.subscribed_addresses.add(address)
            logger.info(f"[WEBSOCKET] Tracking address: {address}")
            return True
        except Exception as e:
            logger.error(f"[WEBSOCKET] Failed to track address {address}: {e}")
            return False
    
    async def handle_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Log the message type (only important messages to reduce spam)
            if isinstance(data, dict):
                message_keys = list(data.keys())
                
                # ADDRESS-SPECIFIC TRANSACTION - This is what we want!
                if 'address-transactions' in data:
                    logger.info(f"🎯 [WEBSOCKET] Received address-specific transaction!")
                    
                    # address-transactions can be a list or a single transaction
                    address_txs = data.get('address-transactions')
                    
                    # If it's a dict, convert to list
                    if isinstance(address_txs, dict):
                        address_txs = [address_txs]
                    
                    # Process each transaction
                    if isinstance(address_txs, list):
                        for tx_item in address_txs:
                            # tx_item might be just a txid string or a dict
                            if isinstance(tx_item, str):
                                txid = tx_item
                            elif isinstance(tx_item, dict):
                                txid = tx_item.get('txid')
                            else:
                                continue
                            
                            if txid:
                                logger.info(f"[WEBSOCKET] Processing transaction: {txid[:16]}...")
                                await self._check_and_process_tx(txid)
                
                # Single transaction with txid
                elif 'txid' in data and 'vout' in data:
                    # This is a full transaction object
                    logger.info(f"[WEBSOCKET] Received full transaction")
                    txid = data.get('txid')
                    
                    if txid:
                        # Check if this transaction involves any of our addresses
                        await self._check_and_process_tx_from_data(txid, data)
                
                # Mempool blocks update
                elif 'mempool-blocks' in data:
                    # Just log, don't process - we'll get address-transactions instead
                    logger.debug(f"[WEBSOCKET] Mempool blocks update")
                
                # Other message types (stats, conversions, blocks, etc.)
                else:
                    # Only log if it's not a known non-transaction message
                    if not any(k in message_keys for k in ['conversions', 'stats', 'live-2h-chart', 'blocks', 'block', 'mempool-blocks']):
                        logger.debug(f"[WEBSOCKET] Other message: {message_keys}")
                
        except json.JSONDecodeError:
            logger.warning(f"[WEBSOCKET] Failed to decode message: {message[:100]}")
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error handling message: {e}")
    
    async def _check_and_process_tx(self, txid: str):
        """Fetch and process transaction by txid"""
        try:
            logger.info(f"[WEBSOCKET] Processing transaction: {txid[:16]}...")
            
            # Get database session
            from .database import get_db
            db = next(get_db())
            
            try:
                # Fetch full transaction details from Mempool.space
                detector = TransactionDetector(db)
                tx_details = await detector.get_transaction_details(txid)
                
                if not tx_details:
                    logger.warning(f"[WEBSOCKET] Could not fetch details for {txid[:16]}...")
                    return
                
                # Process using the transaction data
                await self._check_and_process_tx_from_data(txid, tx_details)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error processing tx {txid[:16] if txid else 'unknown'}: {e}")
    
    async def _broadcast_bet_result(self, bet):
        """Broadcast bet result to frontend WebSocket clients"""
        try:
            # Import manager from main to avoid circular imports
            from .main import manager
            
            # Create bet response data
            bet_data = {
                "id": bet.id,
                "user_address": bet.user.address if bet.user else None,
                "bet_amount": bet.bet_amount,
                "target_multiplier": bet.target_multiplier,
                "win_chance": bet.win_chance,
                "roll_result": bet.roll_result,
                "is_win": bet.is_win,
                "payout_amount": bet.payout_amount,
                "profit": bet.profit,
                "status": bet.status,
                "created_at": bet.created_at.isoformat() if bet.created_at else None,
                "rolled_at": bet.rolled_at.isoformat() if bet.rolled_at else None
            }
            
            # Broadcast to all connected clients
            await manager.broadcast({
                "type": "new_bet",
                "bet": bet_data
            })
            
            logger.info(f"📡 [WEBSOCKET] Broadcast bet {bet.id} result to frontend clients")
            
        except Exception as e:
            logger.error(f"Error broadcasting bet result: {e}")
    
    async def _check_and_process_tx_from_data(self, txid: str, tx_data: dict):
        """Check if transaction involves our addresses and process it"""
        try:
            # Get database session
            from .database import get_db
            db = next(get_db())
            
            try:
                # Check if transaction pays to any of our addresses
                vout = tx_data.get('vout', [])
                
                for addr in list(self.subscribed_addresses):
                    for output in vout:
                        if output.get('scriptpubkey_address') == addr:
                            # Calculate amount
                            amount_sats = output.get('value', 0)
                            amount_btc = amount_sats / 100000000
                            
                            logger.info(f"🎯 [WEBSOCKET] Transaction {txid[:16]}... pays {amount_btc:.8f} BTC to {addr[:10]}...")
                            
                            # Process using manual method
                            detector = TransactionDetector(db)
                            tx = await detector.verify_user_submitted_tx(txid, addr)
                            
                            if tx:
                                logger.info(f"✅ [WEBSOCKET] Transaction saved to database")
                                
                                # Import BetProcessor here to avoid circular imports
                                from .payout import BetProcessor
                                
                                # Process into bet
                                processor = BetProcessor(db)
                                bet = processor.process_detected_transaction(tx)
                                
                                if bet:
                                    result = "WIN 🎉" if bet.is_win else "LOSS"
                                    logger.info(f"🎲 [WEBSOCKET] Bet created: ID {bet.id} - {result}")
                                    logger.info(f"💰 [WEBSOCKET] Amount: {bet.bet_amount} sats, Payout: {bet.payout_amount or 0} sats")
                                    
                                    # Broadcast bet result to frontend via WebSocket
                                    if bet.roll_result is not None:
                                        await self._broadcast_bet_result(bet)
                                
                                return  # Transaction processed, stop checking
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error checking/processing tx data: {e}")
    
    async def listen(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                logger.info(f"[WEBSOCKET] <<<  Message received (length: {len(message)})")
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"[WEBSOCKET] Connection closed: {e.code if hasattr(e, 'code') else 'unknown'}")
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error in listen loop: {e}")
    
    async def start(self):
        """Start WebSocket client with auto-reconnect"""
        self.running = True
        
        while self.running:
            try:
                # Connect
                if await self.connect():
                    # Subscribe to mempool live data
                    await self.subscribe_to_mempool()
                    
                    # Re-track addresses (send track-address for each)
                    if self.subscribed_addresses:
                        logger.info(f"[WEBSOCKET] Re-tracking {len(self.subscribed_addresses)} addresses")
                        for address in list(self.subscribed_addresses):
                            track_msg = {"track-address": address}
                            await self.websocket.send(json.dumps(track_msg))
                    
                    # Listen for messages
                    await self.listen()
                
                # If we get here, connection was lost
                if self.running:
                    logger.warning(f"[WEBSOCKET] Reconnecting in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                    
                    # Increase delay for next reconnect (exponential backoff)
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            
            except Exception as e:
                logger.error(f"[WEBSOCKET] Error in main loop: {e}")
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
    
    def stop(self):
        """Stop WebSocket client"""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
        logger.info("[WEBSOCKET] Stopped")


# Background monitoring service
class TransactionMonitor:
    """
    Transaction monitor service using Mempool.space WebSocket
    
    Uses Mempool.space WebSockets for real-time transaction detection.
    """
    
    def __init__(self, db_session_factory=None):
        self.running = False
        self.websocket_client = None
        self.db_session_factory = db_session_factory
    
    async def start(self):
        """
        Start the monitoring service (WebSocket mode)
        Real-time transaction detection via WebSocket
        """
        self.running = True
        logger.info("[MONITOR] Transaction monitor started (MEMPOOL.SPACE WEBSOCKET MODE)")
        logger.info("[MONITOR] Using Mempool.space WebSocket for real-time detection")
        
        # Create and start WebSocket client
        from .database import get_db
        self.websocket_client = MempoolWebSocket(get_db)
        
        # Subscribe to house address
        asyncio.create_task(self._subscribe_to_house_address())
        
        # Start WebSocket client
        await self.websocket_client.start()
    
    async def _subscribe_to_house_address(self):
        """Subscribe to house address after connection is established"""
        # Wait a bit for connection to be established
        await asyncio.sleep(2)
        
        if self.websocket_client and self.websocket_client.websocket:
            await self.websocket_client.subscribe_address(config.HOUSE_ADDRESS)
            logger.info(f"[MONITOR] Subscribed to house address: {config.HOUSE_ADDRESS}")
    
    async def subscribe_address(self, address: str):
        """Subscribe to a new address"""
        if self.websocket_client:
            await self.websocket_client.subscribe_address(address)
    
    def stop(self):
        """Stop the monitoring service"""
        self.running = False
        if self.websocket_client:
            self.websocket_client.stop()
        logger.info("[SHUTDOWN] Transaction monitor stopped")
