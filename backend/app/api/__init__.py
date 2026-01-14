"""
API Routes - All API endpoints organized by domain
"""
from .websocket_routes import router as websocket_router, manager
from .bet_routes import router as bet_router
from .stats_routes import router as stats_router
from .admin_routes import router as admin_router
from .seed_routes import router as seed_router

__all__ = [
    "websocket_router",
    "bet_router",
    "stats_router",
    "admin_router",
    "seed_router",
    "manager"  # Export WebSocket manager for use in services
]
