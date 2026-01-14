"""
Admin Backend Configuration
Enterprise-grade environment-based configuration using Pydantic Settings
"""
import sys
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from loguru import logger

class AdminSettings(BaseSettings):
    """
    Environment-based admin configuration using Pydantic Settings
    
    ENV_CURRENT: True = Production, False = Test
    Automatically loads different configuration sets based on this toggle
    """
    
    # ============================================================
    # ENVIRONMENT TOGGLE (Single Source of Truth)
    # ============================================================
    ENV_CURRENT: bool = Field(False, description="True = Production, False = Test")
    
    # ============================================================
    # SECURITY
    # ============================================================
    ADMIN_API_KEY: str = Field("", description="Admin API key (32+ chars)")
    ADMIN_IP_WHITELIST: str = Field("127.0.0.1,::1", description="Comma-separated IP whitelist")
    
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
    
    BLOCKSTREAM_API_PROD: str = Field("https://blockstream.info/api", description="Mainnet Blockstream API")
    BLOCKSTREAM_API_TEST: str = Field("https://blockstream.info/testnet/api", description="Testnet Blockstream API")
    
    # ============================================================
    # COLD STORAGE
    # ============================================================
    COLD_STORAGE_ADDRESS_PROD: str = Field("", description="Production cold storage address")
    COLD_STORAGE_ADDRESS_TEST: str = Field("", description="Test cold storage address")
    
    # ============================================================
    # API KEYS (Dynamic)
    # ============================================================
    COINGECKO_API_KEY_PROD: str = Field("", description="CoinGecko Pro API key (production)")
    COINGECKO_API_KEY_TEST: str = Field("", description="CoinGecko Free API key (test)")
    COINGECKO_API_URL: str = Field("https://api.coingecko.com/api/v3", description="CoinGecko API base URL")
    
    # ============================================================
    # SHARED CONFIGURATION
    # ============================================================
    DEFAULT_TX_FEE_SATOSHIS: int = 250
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3001"
    
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
    def BLOCKSTREAM_API(self) -> str:
        """Dynamic Blockstream API based on environment"""
        return self.BLOCKSTREAM_API_PROD if self.ENV_CURRENT else self.BLOCKSTREAM_API_TEST
    
    @property
    def COLD_STORAGE_ADDRESS(self) -> str:
        """Dynamic cold storage address based on environment"""
        return self.COLD_STORAGE_ADDRESS_PROD if self.ENV_CURRENT else self.COLD_STORAGE_ADDRESS_TEST
    
    @property
    def COINGECKO_API_KEY(self) -> str:
        """Dynamic CoinGecko API key based on environment"""
        return self.COINGECKO_API_KEY_PROD if self.ENV_CURRENT else self.COINGECKO_API_KEY_TEST
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def get_ip_whitelist(self) -> List[str]:
        """Parse IP whitelist from comma-separated string"""
        return [ip.strip() for ip in self.ADMIN_IP_WHITELIST.split(',') if ip.strip()]
    
    def validate(self) -> bool:
        """Validate critical admin configuration"""
        errors = []
        
        if not self.ADMIN_API_KEY:
            errors.append("ADMIN_API_KEY is required for admin authentication")
        
        if len(self.ADMIN_API_KEY) < 32:
            errors.append("ADMIN_API_KEY must be at least 32 characters for security")
        
        if not self.MASTER_ENCRYPTION_KEY:
            errors.append("MASTER_ENCRYPTION_KEY is required to decrypt wallet private keys")
        
        if self.ENV_CURRENT and not self.PROD_MASTER_KEY:
            errors.append("PROD_MASTER_KEY is required when ENV_CURRENT=True")
        
        if not self.ENV_CURRENT and not self.TEST_MASTER_KEY:
            errors.append("TEST_MASTER_KEY is required when ENV_CURRENT=False")
        
        if self.ENV_CURRENT and not self.COLD_STORAGE_ADDRESS_PROD:
            errors.append("COLD_STORAGE_ADDRESS_PROD is required in production mode")
        
        if errors:
            raise ValueError(f"Admin configuration errors: {'; '.join(errors)}")
        
        return True
    
    def validate_network_consistency(self) -> bool:
        """Verify Bitcoin network matches environment in production"""
        if not self.ENV_CURRENT:
            logger.info("[ADMIN] Running in TEST mode - skipping network verification")
            return True
        
        logger.info("[ADMIN] Running in PRODUCTION mode - verifying Bitcoin network...")
        
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
                        logger.critical("[ADMIN] FATAL: ENV_CURRENT=True but API is TESTNET!")
                        logger.critical(f"[ADMIN] API URL: {api_url}")
                        logger.critical("[ADMIN] This would cause treasury withdrawals on wrong network!")
                        logger.critical("[ADMIN] Shutting down to prevent disaster...")
                        return False
                    
                    logger.success("[ADMIN] ✓ Bitcoin network verified as MAINNET")
                    return True
            
            result = asyncio.run(check_network())
            if not result:
                sys.exit(1)
            return result
            
        except Exception as e:
            logger.error(f"[ADMIN] Network verification failed: {e}")
            if self.ENV_CURRENT:
                logger.critical("[ADMIN] FATAL: Cannot verify mainnet in production mode!")
                sys.exit(1)
            return False
    
    def print_startup_banner(self):
        """Print visual startup banner indicating environment"""
        mode = "PRODUCTION" if self.ENV_CURRENT else "TEST"
        
        # Use ASCII-safe banner for Windows compatibility
        mode_text = "ADMIN - PRODUCTION MODE" if self.ENV_CURRENT else "ADMIN - TEST MODE"
        separator = "=" * 60
        
        banner = f"""
{separator}
{mode_text:^60}
{separator}
Database:      {self.MONGODB_DB_NAME}
Network:       {self.NETWORK}
Cold Storage:  {self.COLD_STORAGE_ADDRESS if self.COLD_STORAGE_ADDRESS else 'not set'}
API:           {self.MEMPOOL_SPACE_API}
{separator}
"""
        print(banner)
        logger.info(f"[ADMIN CONFIG] Environment: {mode}")
        logger.info(f"[ADMIN CONFIG] Database: {self.MONGODB_DB_NAME}")
        logger.info(f"[ADMIN CONFIG] Bitcoin Network: {self.NETWORK}")
        cold_storage = self.COLD_STORAGE_ADDRESS[:20] if self.COLD_STORAGE_ADDRESS else "not set"
        logger.info(f"[ADMIN CONFIG] Cold Storage: {cold_storage}...")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file


admin_config = AdminSettings()
