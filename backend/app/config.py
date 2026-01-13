"""
Configuration management for the dice game
Loads environment variables and provides type-safe configuration
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # House Wallet - CRITICAL: Never commit real keys
    HOUSE_PRIVATE_KEY: str = os.getenv("HOUSE_PRIVATE_KEY", "")
    HOUSE_ADDRESS: str = os.getenv("HOUSE_ADDRESS", "")
    HOUSE_MNEMONIC: Optional[str] = os.getenv("HOUSE_MNEMONIC")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dice_game.db")
    
    # Game Settings
    HOUSE_EDGE: float = float(os.getenv("HOUSE_EDGE", "0.02"))
    MIN_BET_SATOSHIS: int = int(os.getenv("MIN_BET_SATOSHIS", "600"))  # ~$0.30 at $50k BTC
    MAX_BET_SATOSHIS: int = int(os.getenv("MAX_BET_SATOSHIS", "1000000"))
    MIN_MULTIPLIER: float = float(os.getenv("MIN_MULTIPLIER", "1.1"))
    MAX_MULTIPLIER: float = float(os.getenv("MAX_MULTIPLIER", "98.0"))
    DEFAULT_WIN_CHANCE: float = float(os.getenv("DEFAULT_WIN_CHANCE", "50.0"))
    
    # Bitcoin Network
    CONFIRMATIONS_REQUIRED: int = int(os.getenv("CONFIRMATIONS_REQUIRED", "1"))
    MIN_CONFIRMATIONS_PAYOUT: int = int(os.getenv("MIN_CONFIRMATIONS_PAYOUT", "0"))
    NETWORK: str = os.getenv("NETWORK", "testnet")
    TX_DETECTION_TIMEOUT_MINUTES: int = int(os.getenv("TX_DETECTION_TIMEOUT_MINUTES", "60"))
    
    # Transaction Fees
    DEFAULT_TX_FEE_SATOSHIS: int = int(os.getenv("DEFAULT_TX_FEE_SATOSHIS", "250"))  # Estimated fee for typical transaction
    FEE_BUFFER_SATOSHIS: int = int(os.getenv("FEE_BUFFER_SATOSHIS", "1000"))  # Buffer for UTXO selection
    DUST_LIMIT_SATOSHIS: int = int(os.getenv("DUST_LIMIT_SATOSHIS", "546"))  # Bitcoin dust limit
    
    # API Request Timeouts (seconds)
    API_REQUEST_TIMEOUT: int = int(os.getenv("API_REQUEST_TIMEOUT", "10"))
    BROADCAST_TIMEOUT: int = int(os.getenv("BROADCAST_TIMEOUT", "15"))
    
    # WebSocket Configuration
    WS_PING_INTERVAL: int = int(os.getenv("WS_PING_INTERVAL", "30"))
    WS_PING_TIMEOUT: int = int(os.getenv("WS_PING_TIMEOUT", "20"))
    WS_RECONNECT_DELAY: int = int(os.getenv("WS_RECONNECT_DELAY", "5"))
    WS_MAX_RECONNECT_DELAY: int = int(os.getenv("WS_MAX_RECONNECT_DELAY", "60"))
    
    # API Endpoints
    MEMPOOL_SPACE_API: str = os.getenv("MEMPOOL_SPACE_API", "https://mempool.space/testnet/api")
    MEMPOOL_WEBSOCKET_URL: str = os.getenv("MEMPOOL_WEBSOCKET_URL", "wss://mempool.space/testnet/api/v1/ws")
    BLOCKSTREAM_API: str = os.getenv("BLOCKSTREAM_API", "https://blockstream.info/testnet/api")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    MAX_BETS_PER_USER_PER_HOUR: int = int(os.getenv("MAX_BETS_PER_USER_PER_HOUR", "100"))
    
    # Monitoring
    ENABLE_LOGGING: bool = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "dice_game.log")
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "false").lower() == "true"
    
    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration"""
        errors = []
        
        if not cls.HOUSE_PRIVATE_KEY and not cls.HOUSE_MNEMONIC:
            errors.append("Either HOUSE_PRIVATE_KEY or HOUSE_MNEMONIC is required")
        
        if cls.HOUSE_EDGE < 0 or cls.HOUSE_EDGE >= 1:
            errors.append("HOUSE_EDGE must be between 0 and 1")
        
        if cls.MIN_BET_SATOSHIS <= 0:
            errors.append("MIN_BET_SATOSHIS must be positive")
        
        if cls.MAX_BET_SATOSHIS < cls.MIN_BET_SATOSHIS:
            errors.append("MAX_BET_SATOSHIS must be >= MIN_BET_SATOSHIS")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
        
        return True

# Singleton instance
config = Config()
