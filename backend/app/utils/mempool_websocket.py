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
    
    def add_monitored_address(self, address: str):
        """
        Add address to monitoring list (for filtering mempool data)
        
        Args:
            address: Bitcoin address to monitor
        """
        self.subscribed_addresses.add(address)
        logger.info(f"[WEBSOCKET] 📍 Added to monitoring list: {address[:20]}...")
    
    async def subscribe_to_mempool(self):
        """Subscribe to ALL mempool transactions (live feed)"""
        if not self.websocket:
            logger.warning("[WEBSOCKET] Not connected, cannot subscribe to mempool")
            return
        
        try:
            # Subscribe to mempool transactions feed
            init_msg = {"action": "want", "data": ["blocks", "mempool-blocks", "live-2h-chart"]}
            await self.websocket.send(json.dumps(init_msg))
            
            # Enable tracking for mempool transactions
            await self.websocket.send(json.dumps({"track-mempool": "all"}))
            
            logger.info("[WEBSOCKET] 📊 Subscribed to FULL mempool transaction feed")
            logger.info(f"[WEBSOCKET] 🔍 Monitoring {len(self.subscribed_addresses)} target addresses")
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] Failed to subscribe to mempool: {e}")
    
    async def handle_message(self, message: str):
        """Handle incoming WebSocket message and filter for target addresses"""
        try:
            data = json.loads(message)
            
            # Handle new mempool transaction
            if "tx" in data or "mempoolInfo" in data:
                # Extract transaction data
                tx_data = data.get("tx") or data.get("mempoolInfo")
                
                if tx_data and isinstance(tx_data, dict):
                    await self._check_transaction_for_targets(tx_data)
            
            # Handle blocks/mempool-blocks (ignore)
            elif "mempool-blocks" in data or "blocks" in data or "live-2h-chart" in data:
                pass  # Ignore block/chart updates
            
            # Handle other transaction formats
            elif isinstance(data, dict):
                # Check if this is transaction data
                if "txid" in data or "vout" in data:
                    await self._check_transaction_for_targets(data)
                else:
                    logger.debug(f"[WEBSOCKET] Other message type: {list(data.keys())}")
                
        except json.JSONDecodeError:
            logger.warning(f"[WEBSOCKET] Failed to parse message as JSON")
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error handling message: {e}")
    
    async def _check_transaction_for_targets(self, tx_data: dict):
        """
        Check if transaction involves any of our target addresses
        
        Args:
            tx_data: Transaction data from mempool
        """
        try:
            # Extract txid
            txid = tx_data.get('txid')
            if not txid:
                return
            
            # Get outputs
            vout = tx_data.get('vout', [])
            if not vout:
                return
            
            # Check each output against our monitored addresses
            for output in vout:
                output_address = output.get('scriptpubkey_address') or output.get('address')
                
                if output_address in self.subscribed_addresses:
                    # MATCH FOUND! Transaction pays to one of our wallets
                    amount_sats = output.get('value', 0)
                    amount_btc = amount_sats / 100_000_000
                    
                    logger.info(f"🎯 [MEMPOOL FILTER] MATCH! TX {txid[:16]}... → {output_address[:10]}... ({amount_btc:.8f} BTC)")
                    
                    # Process this transaction
                    await self._process_transaction(txid)
                    return  # Only process once per transaction
                    
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error checking transaction for targets: {e}")
    
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
                    # Subscribe to FULL mempool feed
                    await self.subscribe_to_mempool()
                    
                    logger.info(f"[WEBSOCKET] 🔍 Filtering for {len(self.subscribed_addresses)} target addresses")
                    
                    # Listen for messages and filter
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
