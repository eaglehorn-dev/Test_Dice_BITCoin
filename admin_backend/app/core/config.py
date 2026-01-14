"""
Admin Backend Configuration
Separate from the main dice game backend for security isolation
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class AdminConfig:
    """Admin system configuration"""
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")
    ADMIN_IP_WHITELIST: str = os.getenv("ADMIN_IP_WHITELIST", "127.0.0.1,::1")
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "dice_game")
    
    MASTER_ENCRYPTION_KEY: str = os.getenv("MASTER_ENCRYPTION_KEY", "")
    
    NETWORK: str = os.getenv("NETWORK", "mainnet")
    COLD_STORAGE_ADDRESS: str = os.getenv("COLD_STORAGE_ADDRESS", "")
    
    COINGECKO_API_URL: str = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
    MEMPOOL_SPACE_API: str = os.getenv("MEMPOOL_SPACE_API", "https://mempool.space/api")
    BLOCKSTREAM_API: str = os.getenv("BLOCKSTREAM_API", "https://blockstream.info/api")
    
    DEFAULT_TX_FEE_SATOSHIS: int = int(os.getenv("DEFAULT_TX_FEE_SATOSHIS", "250"))
    
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3001")
    
    @classmethod
    def get_ip_whitelist(cls) -> List[str]:
        """Parse IP whitelist from comma-separated string"""
        return [ip.strip() for ip in cls.ADMIN_IP_WHITELIST.split(',') if ip.strip()]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical admin configuration"""
        errors = []
        
        if not cls.ADMIN_API_KEY:
            errors.append("ADMIN_API_KEY is required for admin authentication")
        
        if len(cls.ADMIN_API_KEY) < 32:
            errors.append("ADMIN_API_KEY must be at least 32 characters for security")
        
        if not cls.MASTER_ENCRYPTION_KEY:
            errors.append("MASTER_ENCRYPTION_KEY is required to decrypt wallet private keys")
        
        if not cls.COLD_STORAGE_ADDRESS:
            errors.append("COLD_STORAGE_ADDRESS is required for treasury withdrawals")
        
        if errors:
            raise ValueError(f"Admin configuration errors: {'; '.join(errors)}")
        
        return True

admin_config = AdminConfig()
