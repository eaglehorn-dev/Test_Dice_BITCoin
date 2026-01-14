"""
FastAPI Main Application
REST API for Bitcoin Dice Game - DDD Architecture with MongoDB
"""
import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import config
from app.models.database import init_db, disconnect_db
from app.services.transaction_monitor_service import TransactionMonitorService
from app.api import websocket_router, bet_router, stats_router, admin_router, seed_router, manager

# Setup Loguru logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.LOG_LEVEL,
    colorize=True
)

if config.ENABLE_LOGGING:
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )

# Global transaction monitor
tx_monitor: TransactionMonitorService = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("[STARTUP] Starting Bitcoin Dice Game API")
    
    # Validate configuration
    try:
        config.validate()
        logger.info("[OK] Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise
    
    # Initialize database
    await init_db()
    logger.info("[OK] Database initialized")
    
    # Start transaction monitor (Mempool.space WebSocket mode)
    global tx_monitor
    tx_monitor = TransactionMonitorService()
    await tx_monitor.start()
    logger.info("[OK] Transaction monitor started")
    
    yield
    
    # Shutdown
    logger.info("[SHUTDOWN] Shutting down Bitcoin Dice Game API")
    if tx_monitor:
        await tx_monitor.stop()
    await disconnect_db()


# Create FastAPI app
app = FastAPI(
    title="Bitcoin Dice Game API",
    description="Provably Fair Bitcoin Dice Game with DDD Architecture",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow all origins for development/public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(websocket_router)  # WebSocket routes
app.include_router(bet_router)        # Bet endpoints
app.include_router(stats_router)      # Statistics endpoints
app.include_router(admin_router)      # Admin endpoints
app.include_router(seed_router)       # Seed verification endpoints


@app.get("/")
async def root():
    """API Root endpoint"""
    return {
        "name": "Bitcoin Dice Game API",
        "version": "2.0.0",
        "architecture": "Domain-Driven Design (DDD)",
        "database": "MongoDB",
        "network": config.NETWORK,
        "status": "running",
        "endpoints": {
            "bets": "/api/bets",
            "stats": "/api/stats",
            "admin": "/api/admin",
            "seeds": "/api/seeds",
            "websocket": "/ws",
            "docs": "/docs"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "monitor": "running" if tx_monitor and tx_monitor.is_running() else "stopped",
        "network": config.NETWORK,
        "house_address": config.HOUSE_ADDRESS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD
    )
