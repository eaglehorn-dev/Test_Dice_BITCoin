"""
Configuration management for the dice game
Enterprise-grade environment-based configuration using Pydantic Settings
"""
import sys
import httpx
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from loguru import logger

class Settings(BaseSettings):
    """
    Environment-based configuration using Pydantic Settings
    
    ENV_CURRENT: True = Production, False = Test
    Automatically loads different configuration sets based on this toggle
    """
    
    # ============================================================
    # ENVIRONMENT TOGGLE (Single Source of Truth)
    # ============================================================
    ENV_CURRENT: bool = Field(False, description="True = Production, False = Test")
    
    # ============================================================
    # DATABASE CONFIGURATION (Dynamic)
    # ============================================================
    MONGODB_URL_PROD: str = Field("mongodb://localhost:27017", description="Production MongoDB")
    MONGODB_URL_TEST: str = Field("mongodb://localhost:27017", description="Test MongoDB")
    MONGODB_DB_NAME_PROD: str = Field("dice_prod", description="Production database name")
    MONGODB_DB_NAME_TEST: str = Field("dice_test", description="Test database name")
    
    # ============================================================
    # WALLET ENCRYPTION KEYS (Dynamic)
    # ============================================================
    PROD_MASTER_KEY: str = Field("", description="Production master encryption key")
    TEST_MASTER_KEY: str = Field("", description="Test master encryption key")
    
    # ============================================================
    # BITCOIN NETWORK CONFIGURATION (Dynamic)
    # ============================================================
    BTC_NETWORK_PROD: str = Field("mainnet", description="Production Bitcoin network")
    BTC_NETWORK_TEST: str = Field("testnet", description="Test Bitcoin network")
    
    MEMPOOL_API_PROD: str = Field("https://mempool.space/api", description="Mainnet Mempool API")
    MEMPOOL_API_TEST: str = Field("https://mempool.space/testnet/api", description="Testnet Mempool API")
    
    MEMPOOL_WS_PROD: str = Field("wss://mempool.space/api/v1/ws", description="Mainnet Mempool WebSocket")
    MEMPOOL_WS_TEST: str = Field("wss://mempool.space/testnet/api/v1/ws", description="Testnet Mempool WebSocket")
    
    BLOCKSTREAM_API_PROD: str = Field("https://blockstream.info/api", description="Mainnet Blockstream API")
    BLOCKSTREAM_API_TEST: str = Field("https://blockstream.info/testnet/api", description="Testnet Blockstream API")
    
    # ============================================================
    # API KEYS (Dynamic)
    # ============================================================
    COINGECKO_API_KEY_PROD: str = Field("", description="CoinGecko Pro API key (production)")
    COINGECKO_API_KEY_TEST: str = Field("", description="CoinGecko Free API key (test)")
    COINGECKO_API_URL: str = Field("https://api.coingecko.com/api/v3", description="CoinGecko API base URL")
    
    # ============================================================
    # GAME CONFIGURATION
    # ============================================================
    HOUSE_EDGE: float = 0.02
    MIN_BET_SATOSHIS: int = 600
    MAX_BET_SATOSHIS: int = 1000000
    MIN_MULTIPLIER: float = 1.1
    MAX_MULTIPLIER: float = 98.0
    DEFAULT_WIN_CHANCE: float = 50.0
    
    CONFIRMATIONS_REQUIRED: int = 1
    MIN_CONFIRMATIONS_PAYOUT: int = 0
    TX_DETECTION_TIMEOUT_MINUTES: int = 60
    
    DEFAULT_TX_FEE_SATOSHIS: int = 250
    FEE_BUFFER_SATOSHIS: int = 1000
    DUST_LIMIT_SATOSHIS: int = 546
    
    API_REQUEST_TIMEOUT: int = 10
    BROADCAST_TIMEOUT: int = 15
    
    WS_PING_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 20
    WS_RECONNECT_DELAY: int = 5
    WS_MAX_RECONNECT_DELAY: int = 60
    
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_BETS_PER_USER_PER_HOUR: int = 100
    
    ENABLE_LOGGING: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "dice_game.log"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    DEBUG: bool = False
    
    FRONTEND_URL: str = "http://localhost:3000"
    
    # ============================================================
    # DYNAMIC PROPERTIES (Automatically switch based on ENV_CURRENT)
    # ============================================================
    
    @property
    def MONGODB_URL(self) -> str:
        """Dynamic MongoDB URL based on environment"""
        return self.MONGODB_URL_PROD if self.ENV_CURRENT else self.MONGODB_URL_TEST
    
    @property
    def MONGODB_DB_NAME(self) -> str:
        """Dynamic database name based on environment"""
        return self.MONGODB_DB_NAME_PROD if self.ENV_CURRENT else self.MONGODB_DB_NAME_TEST
    
    @property
    def MASTER_ENCRYPTION_KEY(self) -> str:
        """Dynamic encryption key based on environment"""
        return self.PROD_MASTER_KEY if self.ENV_CURRENT else self.TEST_MASTER_KEY
    
    @property
    def NETWORK(self) -> str:
        """Dynamic Bitcoin network based on environment"""
        return self.BTC_NETWORK_PROD if self.ENV_CURRENT else self.BTC_NETWORK_TEST
    
    @property
    def MEMPOOL_SPACE_API(self) -> str:
        """Dynamic Mempool API based on environment"""
        return self.MEMPOOL_API_PROD if self.ENV_CURRENT else self.MEMPOOL_API_TEST
    
    @property
    def MEMPOOL_WEBSOCKET_URL(self) -> str:
        """Dynamic Mempool WebSocket based on environment"""
        return self.MEMPOOL_WS_PROD if self.ENV_CURRENT else self.MEMPOOL_WS_TEST
    
    @property
    def BLOCKSTREAM_API(self) -> str:
        """Dynamic Blockstream API based on environment"""
        return self.BLOCKSTREAM_API_PROD if self.ENV_CURRENT else self.BLOCKSTREAM_API_TEST
    
    # ============================================================
    # VALIDATION & SAFETY CHECKS
    # ============================================================
    
    def validate_network_consistency(self) -> bool:
        """
        CRITICAL: Verify that the Bitcoin node is actually on the expected network
        If in production mode but connected to testnet, this prevents financial loss
        """
        if not self.ENV_CURRENT:
            logger.info("[VALIDATION] Running in TEST mode - skipping network verification")
            return True
        
        logger.info("[VALIDATION] Running in PRODUCTION mode - verifying Bitcoin network...")
        
        try:
            import httpx
            import asyncio
            
            async def check_network():
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(f"{self.MEMPOOL_SPACE_API}/blocks/tip/height")
                    response.raise_for_status()
                    
                    api_url = str(response.url)
                    is_mainnet_api = "mempool.space/api" in api_url and "/testnet" not in api_url
                    
                    if not is_mainnet_api:
                        logger.critical("[VALIDATION] FATAL: ENV_CURRENT=True but API is TESTNET!")
                        logger.critical(f"[VALIDATION] API URL: {api_url}")
                        logger.critical("[VALIDATION] This would cause real money loss on testnet!")
                        logger.critical("[VALIDATION] Shutting down to prevent financial disaster...")
                        return False
                    
                    logger.success("[VALIDATION] ✓ Bitcoin network verified as MAINNET")
                    logger.success(f"[VALIDATION] Current block height: {response.text}")
                    return True
            
            result = asyncio.run(check_network())
            if not result:
                sys.exit(1)
            return result
            
        except Exception as e:
            logger.error(f"[VALIDATION] Network verification failed: {e}")
            if self.ENV_CURRENT:
                logger.critical("[VALIDATION] FATAL: Cannot verify mainnet in production mode!")
                sys.exit(1)
            return False
    
    def validate(self) -> bool:
        """Validate critical configuration"""
        errors = []
        
        if not self.MASTER_ENCRYPTION_KEY:
            errors.append("MASTER_ENCRYPTION_KEY is required for wallet vault encryption")
        
        if self.ENV_CURRENT and not self.PROD_MASTER_KEY:
            errors.append("PROD_MASTER_KEY is required when ENV_CURRENT=True")
        
        if not self.ENV_CURRENT and not self.TEST_MASTER_KEY:
            errors.append("TEST_MASTER_KEY is required when ENV_CURRENT=False")
        
        if self.HOUSE_EDGE < 0 or self.HOUSE_EDGE >= 1:
            errors.append("HOUSE_EDGE must be between 0 and 1")
        
        if self.MIN_BET_SATOSHIS <= 0:
            errors.append("MIN_BET_SATOSHIS must be positive")
        
        if self.MAX_BET_SATOSHIS < self.MIN_BET_SATOSHIS:
            errors.append("MAX_BET_SATOSHIS must be >= MIN_BET_SATOSHIS")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
        
        return True
    
    def print_startup_banner(self):
        """Print visual startup banner indicating environment"""
        mode = "PRODUCTION" if self.ENV_CURRENT else "TEST"
        color_code = "\033[91m" if self.ENV_CURRENT else "\033[93m"  # Red for prod, Yellow for test
        reset_code = "\033[0m"
        
        banner = f"""
{color_code}
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║  {'🚨 RUNNING IN PRODUCTION MODE 🚨' if self.ENV_CURRENT else '🧪 RUNNING IN TEST MODE 🧪':^56}  ║
║                                                          ║
║  Database: {self.MONGODB_DB_NAME:<44}  ║
║  Network:  {self.NETWORK:<44}  ║
║  API:      {self.MEMPOOL_SPACE_API[:44]:<44}  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
{reset_code}
"""
        print(banner)
        logger.info(f"[CONFIG] Environment: {mode}")
        logger.info(f"[CONFIG] Database: {self.MONGODB_DB_NAME}")
        logger.info(f"[CONFIG] Bitcoin Network: {self.NETWORK}")
    
    class Config:
        """Pydantic Settings configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
config = settings  # Backwards compatibility alias
