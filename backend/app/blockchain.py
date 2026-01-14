"""
Transaction Detection System using Mempool.space API
Real-time monitoring via WebSocket and REST API - MongoDB Version
"""
import asyncio
import json
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
import httpx
import websockets
from loguru import logger
from bson import ObjectId

from app.core.config import config
from app.core.exceptions import BlockchainException, WebSocketException
from app.models.database import (
    get_transactions_collection,
    get_deposit_addresses_collection,
    get_users_collection
)
from app.models import TransactionModel, DepositAddressModel


class TransactionDetector:
    """
    Transaction detection system using Mempool.space API
    
    Uses Mempool.space REST API for transaction detection and verification
    """
    
    def __init__(self):
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
            tx_col = get_transactions_collection()
            
            # Check if already exists
            existing = await tx_col.find_one({"txid": txid})
            
            if existing:
                logger.info(f"[TX] Transaction {txid[:16]}... already in database")
                return existing
            
            # Get transaction details from Mempool.space
            tx_data = await self.get_transaction_details(txid)
            
            if not tx_data:
                logger.warning(f"[TX] Transaction {txid} not found")
                return None
            
            # Process and store the transaction
            tx_obj = await self._process_mempool_tx(tx_data, expected_address, 'user_submitted')
            return tx_obj
            
        except Exception as e:
            logger.error(f"Error verifying user-submitted tx: {e}")
            return None
    
    async def check_address_transactions(self, address: str) -> List[Dict[str, Any]]:
        """
        Check Mempool.space API for new transactions to an address
        
        Args:
            address: Bitcoin address to check
            
        Returns:
            List of new transaction documents
        """
        new_transactions = []
        
        try:
            tx_col = get_transactions_collection()
            
            # Get transactions from Mempool.space
            mempool_txs = await self.check_mempool_space_api(address)
            
            for tx_data in mempool_txs:
                tx_hash = tx_data.get('txid')
                
                if not tx_hash:
                    continue
                
                # Check if already exists
                existing = await tx_col.find_one({"txid": tx_hash})
                
                if existing:
                    continue
                
                # Convert to our format and store
                tx_obj = await self._process_mempool_tx(tx_data, address, 'mempool_space')
                if tx_obj:
                    new_transactions.append(tx_obj)
            
            if new_transactions:
                logger.info(f"[MEMPOOL] Found {len(new_transactions)} new tx(s)")
            
            return new_transactions
            
        except Exception as e:
            logger.error(f"Error checking address transactions: {e}")
            return []
    
    async def _process_mempool_tx(
        self,
        tx_data: Dict[str, Any],
        address: str,
        source: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a transaction from Mempool.space into our database format
        
        Args:
            tx_data: Transaction data from Mempool.space
            address: Target address
            source: Detection source
            
        Returns:
            Transaction document or None
        """
        try:
            tx_col = get_transactions_collection()
            
            txid = tx_data.get('txid')
            
            # Extract amount sent to target address
            amount = 0
            vout = tx_data.get('vout', [])
            
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
            return None


# Mempool.space WebSocket client
class MempoolWebSocket:
    """
    WebSocket client for Mempool.space real-time transaction monitoring
    MongoDB version
    """
    
    def __init__(self):
        self.websocket = None
        self.running = False
        self.subscribed_addresses: Set[str] = set()
        self.reconnect_delay = config.WS_RECONNECT_DELAY
        self.max_reconnect_delay = config.WS_MAX_RECONNECT_DELAY
    
    async def connect(self) -> bool:
        """Connect to Mempool.space WebSocket"""
        try:
            logger.info(f"[WEBSOCKET] Connecting to {config.MEMPOOL_WEBSOCKET_URL}...")
            
            self.websocket = await websockets.connect(
                config.MEMPOOL_WEBSOCKET_URL,
                ping_interval=config.WS_PING_INTERVAL,
                ping_timeout=config.WS_PING_TIMEOUT
            )
            
            # Reset reconnect delay on successful connection
            self.reconnect_delay = config.WS_RECONNECT_DELAY
            
            logger.info("[WEBSOCKET] ✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] Connection failed: {e}")
            return False
    
    async def subscribe_address(self, address: str):
        """
        Subscribe to a specific Bitcoin address for transaction updates
        
        Args:
            address: Bitcoin address to track
        """
        if not self.websocket:
            logger.warning("[WEBSOCKET] Not connected, cannot subscribe")
            return
        
        try:
            # Send track-address message
            track_msg = {"track-address": address}
            await self.websocket.send(json.dumps(track_msg))
            
            # Add to subscribed set
            self.subscribed_addresses.add(address)
            
            logger.info(f"[WEBSOCKET] 📍 Tracking address: {address[:20]}...")
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] Failed to subscribe to {address}: {e}")
    
    async def subscribe_to_mempool(self):
        """Subscribe to mempool live updates"""
        if not self.websocket:
            logger.warning("[WEBSOCKET] Not connected, cannot subscribe to mempool")
            return
        
        try:
            init_msg = {"action": "want", "data": ["blocks", "mempool-blocks"]}
            await self.websocket.send(json.dumps(init_msg))
            logger.info("[WEBSOCKET] 📊 Subscribed to mempool updates")
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] Failed to subscribe to mempool: {e}")
    
    async def handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Handle address-transactions messages (our target)
            if "address-transactions" in data:
                address_txs = data["address-transactions"]
                
                # Handle both list and dict formats
                if isinstance(address_txs, list):
                    for tx in address_txs:
                        if isinstance(tx, dict):
                            txid = tx.get('txid')
                            if txid:
                                await self._process_transaction(txid)
                        elif isinstance(tx, str):
                            await self._process_transaction(tx)
                elif isinstance(address_txs, dict):
                    txid = address_txs.get('txid')
                    if txid:
                        await self._process_transaction(txid)
                elif isinstance(address_txs, str):
                    await self._process_transaction(address_txs)
            
            # Log other message types for debugging
            elif "mempool-blocks" in data or "blocks" in data:
                pass  # Ignore mempool/block updates
            else:
                logger.debug(f"[WEBSOCKET] Other message type: {list(data.keys())}")
                
        except json.JSONDecodeError:
            logger.warning(f"[WEBSOCKET] Failed to parse message as JSON")
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error handling message: {e}")
    
    async def _process_transaction(self, txid: str):
        """Process a transaction detected via WebSocket"""
        try:
            logger.info(f"[WEBSOCKET] 🔔 New transaction detected: {txid[:16]}...")
            
            # Fetch full transaction details from Mempool.space
            detector = TransactionDetector()
            tx_details = await detector.get_transaction_details(txid)
            
            if not tx_details:
                logger.warning(f"[WEBSOCKET] Could not fetch details for {txid[:16]}...")
                return
            
            # Process using the transaction data
            await self._check_and_process_tx_from_data(txid, tx_details)
                
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error processing tx {txid[:16] if txid else 'unknown'}: {e}")
    
    async def _broadcast_bet_result(self, bet: Dict[str, Any]):
        """Broadcast bet result to frontend WebSocket clients"""
        try:
            # Import manager from main to avoid circular imports
            from .main import manager
            from .database import get_users_collection
            
            # Get user address
            users_col = get_users_collection()
            user = await users_col.find_one({"_id": ObjectId(bet["user_id"])})
            
            # Create bet response data
            bet_data = {
                "id": str(bet["_id"]),
                "user_address": user["address"] if user else None,
                "bet_amount": bet["bet_amount"],
                "target_multiplier": bet["target_multiplier"],
                "win_chance": bet["win_chance"],
                "roll_result": bet.get("roll_result"),
                "is_win": bet.get("is_win"),
                "payout_amount": bet.get("payout_amount"),
                "profit": bet.get("profit"),
                "status": bet["status"],
                "created_at": bet["created_at"].isoformat() if bet.get("created_at") else None,
                "rolled_at": bet.get("rolled_at").isoformat() if bet.get("rolled_at") else None
            }
            
            # Broadcast to all connected clients
            await manager.broadcast({
                "type": "new_bet",
                "bet": bet_data
            })
            
            logger.info(f"📡 [WEBSOCKET] Broadcast bet {bet['_id']} result to frontend clients")
            
        except Exception as e:
            logger.error(f"Error broadcasting bet result: {e}")
    
    async def _check_and_process_tx_from_data(self, txid: str, tx_data: dict):
        """Check if transaction involves our addresses and process it"""
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
                        detector = TransactionDetector()
                        tx = await detector.verify_user_submitted_tx(txid, addr)
                        
                        if tx:
                            logger.info(f"✅ [WEBSOCKET] Transaction saved to database")
                            
                            # Import BetService here to avoid circular imports
                            from app.services.bet_service import BetService
                            
                            # Process into bet
                            bet_service = BetService()
                            bet = await bet_service.process_detected_transaction(tx)
                            
                            if bet:
                                result = "WIN 🎉" if bet.get("is_win") else "LOSS"
                                logger.info(f"🎲 [WEBSOCKET] Bet created: ID {bet['_id']} - {result}")
                                logger.info(f"💰 [WEBSOCKET] Amount: {bet['bet_amount']} sats, Payout: {bet.get('payout_amount', 0)} sats")
                                
                                # Broadcast bet result to frontend via WebSocket
                                if bet.get("roll_result") is not None:
                                    await self._broadcast_bet_result(bet)
                            
                            return  # Transaction processed, stop checking
                
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
    MongoDB version
    
    Uses Mempool.space WebSockets for real-time transaction detection.
    """
    
    def __init__(self):
        self.running = False
        self.websocket_client = None
    
    async def start(self):
        """
        Start the monitoring service (WebSocket mode)
        Real-time transaction detection via WebSocket
        """
        self.running = True
        logger.info("[MONITOR] Transaction monitor started (MEMPOOL.SPACE WEBSOCKET MODE)")
        logger.info("[MONITOR] Using Mempool.space WebSocket for real-time detection")
        
        # Create and start WebSocket client
        self.websocket_client = MempoolWebSocket()
        
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
