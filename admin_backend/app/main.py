"""
Admin Backend - Secure Management System for Bitcoin Dice Game
Runs on separate port (8001) with API key + IP whitelist authentication
"""
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import admin_config
from app.utils.database import connect_db, disconnect_db
from app.api.admin_routes import router as admin_router

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)
logger.add(
    "admin_backend.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("=" * 60)
    logger.info("🔐 ADMIN BACKEND STARTING")
    logger.info("=" * 60)
    
    # Print environment banner
    admin_config.print_startup_banner()
    
    try:
        admin_config.validate()
        logger.success("[CONFIG] Configuration validated")
    except Exception as e:
        logger.error(f"[CONFIG] Validation failed: {e}")
        raise
    
    # CRITICAL: Verify network consistency in production
    if admin_config.ENV_CURRENT:
        logger.warning("[SECURITY] Production mode detected - verifying network...")
        admin_config.validate_network_consistency()
    
    await connect_db()
    logger.success("[DATABASE] Connected to MongoDB")
    
    logger.info(f"[SERVER] Admin API running on {admin_config.HOST}:{admin_config.PORT}")
    logger.info(f"[SECURITY] IP Whitelist: {admin_config.get_ip_whitelist()}")
    logger.warning("[SECURITY] All /admin routes protected by API key + IP whitelist")
    
    yield
    
    logger.info("🛑 ADMIN BACKEND SHUTTING DOWN")
    await disconnect_db()

app = FastAPI(
    title="Bitcoin Dice Admin API",
    description="Secure admin backend for managing Bitcoin dice game",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[admin_config.FRONTEND_URL, "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Bitcoin Dice Admin Backend",
        "version": "1.0.0",
        "status": "operational",
        "note": "All /admin endpoints require authentication"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=admin_config.HOST,
        port=admin_config.PORT,
        reload=admin_config.DEBUG
    )
