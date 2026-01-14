"""
WebSocket Connection Manager
Centralized WebSocket state management for frontend connections
"""
from typing import List, Dict, Set
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_address: str = None):
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_address: Optional user Bitcoin address
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "address": user_address,
            "connected_at": None  # Add timestamp if needed
        }
        logger.info(f"[WS] New connection (Total: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"[WS] Connection closed (Total: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """
        Send message to a specific connection
        
        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"[WS] Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict, exclude: Set[WebSocket] = None):
        """
        Broadcast message to all connected clients
        
        Args:
            message: Message dictionary to send
            exclude: Set of WebSocket connections to exclude from broadcast
        """
        if exclude is None:
            exclude = set()
        
        disconnected = []
        
        for connection in self.active_connections:
            if connection in exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"[WS] Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_bet_result(self, bet_data: Dict):
        """
        Broadcast bet result to all connected clients
        
        Args:
            bet_data: Bet result data
        """
        message = {
            "type": "bet_result",
            "data": {
                "bet_id": str(bet_data.get("_id")),
                "user_address": bet_data.get("user_address", "Anonymous")[:10] + "...",
                "bet_amount": bet_data.get("bet_amount"),
                "multiplier": bet_data.get("target_multiplier"),
                "roll": bet_data.get("roll_result"),
                "is_win": bet_data.get("is_win"),
                "payout": bet_data.get("payout_amount"),
                "profit": bet_data.get("profit")
            }
        }
        await self.broadcast(message)
    
    async def send_user_notification(self, user_address: str, notification: Dict):
        """
        Send notification to specific user by address
        
        Args:
            user_address: User's Bitcoin address
            notification: Notification data
        """
        for connection, info in self.connection_info.items():
            if info.get("address") == user_address:
                await self.send_personal_message(notification, connection)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_user_connections(self, user_address: str) -> List[WebSocket]:
        """Get all connections for a specific user"""
        connections = []
        for connection, info in self.connection_info.items():
            if info.get("address") == user_address:
                connections.append(connection)
        return connections
