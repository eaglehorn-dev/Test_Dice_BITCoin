"""
Transaction Monitor Service - Orchestrates real-time transaction monitoring
"""
import asyncio
from loguru import logger

from app.core.config import config
from app.utils.mempool_websocket import MempoolWebSocket
from app.services.wallet_service import WalletService


class TransactionMonitorService:
    """
    Background monitoring service for Bitcoin transactions
    Orchestrates WebSocket monitoring for all vault wallets
    """
    
    def __init__(self):
        self.websocket_client = MempoolWebSocket()
        self.wallet_service = WalletService()
        self.running = False
        self.monitor_task = None
        self.monitored_addresses = set()
    
    async def start(self):
        """Start the transaction monitor"""
        if self.running:
            logger.warning("[MONITOR] Already running")
            return
        
        self.running = True
        logger.info("[MONITOR] 🚀 Starting transaction monitor...")
        
        # Get all active vault wallets
        active_wallets = await self.wallet_service.get_active_wallets()
        
        if not active_wallets:
            logger.warning("[MONITOR] ⚠️ No active vault wallets found!")
            logger.warning("[MONITOR] Run the admin script to create wallets first")
            return
        
        # Subscribe to all vault wallet addresses
        for wallet in active_wallets:
            address = wallet["address"]
            multiplier = wallet["multiplier"]
            await self.websocket_client.subscribe_address(address)
            self.monitored_addresses.add(address)
            logger.info(f"[MONITOR] 📍 Monitoring {multiplier}x wallet: {address[:20]}...")
        
        # Start WebSocket client in background
        self.monitor_task = asyncio.create_task(self.websocket_client.start())
        
        logger.info(f"[MONITOR] ✅ Monitoring {len(active_wallets)} vault wallet(s)")
    
    async def stop(self):
        """Stop the transaction monitor"""
        if not self.running:
            return
        
        logger.info("[MONITOR] 🛑 Stopping transaction monitor...")
        
        self.running = False
        self.websocket_client.stop()
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[MONITOR] ✅ Transaction monitor stopped")
    
    def is_running(self) -> bool:
        """Check if monitor is running"""
        return self.running
    
    async def subscribe_address(self, address: str):
        """Subscribe to additional address"""
        await self.websocket_client.subscribe_address(address)
        logger.info(f"[MONITOR] 📍 Added address to monitoring: {address[:20]}...")
