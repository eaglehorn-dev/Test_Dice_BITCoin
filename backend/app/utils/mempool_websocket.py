"""
Mempool.space WebSocket client for real-time transaction monitoring
"""
import asyncio
import json
from typing import Set, Dict, Any
import websockets
from loguru import logger
from bson import ObjectId

from app.core.config import config
from app.core.exceptions import WebSocketException


class MempoolWebSocket:
    """
    WebSocket client for Mempool.space real-time transaction monitoring
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
            raise WebSocketException(f"Failed to connect: {str(e)}")
    
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
            raise WebSocketException(f"Failed to subscribe: {str(e)}")
    
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
            
            # Import services here to avoid circular imports
            from app.services.transaction_service import TransactionService
            from app.services.bet_service import BetService
            
            # Fetch full transaction details
            tx_service = TransactionService()
            tx_details = await tx_service.get_transaction_details(txid)
            
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
            # Import manager from utils to avoid circular imports
            from app.utils.websocket_manager import manager
            from app.models.database import get_users_collection
            
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
            from app.services.transaction_service import TransactionService
            from app.services.bet_service import BetService
            
            # Check if transaction pays to any of our addresses
            vout = tx_data.get('vout', [])
            
            for addr in list(self.subscribed_addresses):
                for output in vout:
                    if output.get('scriptpubkey_address') == addr:
                        # Calculate amount
                        amount_sats = output.get('value', 0)
                        amount_btc = amount_sats / 100000000
                        
                        logger.info(f"🎯 [WEBSOCKET] Transaction {txid[:16]}... pays {amount_btc:.8f} BTC to {addr[:10]}...")
                        
                        # Process using transaction service
                        tx_service = TransactionService()
                        tx = await tx_service.verify_user_submitted_tx(txid, addr)
                        
                        if tx:
                            logger.info(f"✅ [WEBSOCKET] Transaction saved to database")
                            
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
                    
                    # Re-track addresses
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
                    
                    # Exponential backoff
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
