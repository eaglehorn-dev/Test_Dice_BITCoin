"""
WebSocket routes for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from loguru import logger

from app.utils.websocket_manager import manager

router = APIRouter()


async def handle_websocket_connection(websocket: WebSocket):
    """
    Handle WebSocket connection for real-time bet updates
    
    Clients connect here to receive:
    - New bet notifications
    - Bet results
    - Game statistics updates
    """
    # manager.connect() already calls websocket.accept()
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Handle ping messages
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "message": "Connected to Bitcoin Dice Game"
                })
            else:
                # Echo back other messages
                await websocket.send_json({
                    "type": "echo",
                    "data": data
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("[WS] Client disconnected")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint at /ws"""
    await handle_websocket_connection(websocket)


@router.websocket("/ws/bets")
async def websocket_bets_endpoint(websocket: WebSocket):
    """WebSocket endpoint at /ws/bets (for frontend compatibility)"""
    await handle_websocket_connection(websocket)
