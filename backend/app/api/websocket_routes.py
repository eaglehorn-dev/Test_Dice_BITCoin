"""
WebSocket routes for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.utils.websocket_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bet updates
    
    Clients connect here to receive:
    - New bet notifications
    - Bet results
    - Game statistics updates
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            
            # Echo back or handle specific commands
            await websocket.send_json({
                "type": "pong",
                "message": "Connected to Bitcoin Dice Game"
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("[WS] Client disconnected")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
        manager.disconnect(websocket)
