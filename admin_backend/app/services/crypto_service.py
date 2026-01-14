"""
Crypto Service (Shared with Main Backend)
Encrypts/Decrypts wallet private keys using Fernet (AES-256)
"""
from cryptography.fernet import Fernet, InvalidToken
from loguru import logger
from app.core.config import admin_config

class CryptoService:
    """Handles encryption and decryption for wallet vault"""
    
    def __init__(self):
        self._fernet = None
        self._load_key()
    
    def _load_key(self):
        """Load master encryption key from config"""
        master_key = admin_config.MASTER_ENCRYPTION_KEY
        if not master_key:
            raise ValueError("MASTER_ENCRYPTION_KEY not configured")
        
        logger.info(f"[CRYPTO] Loading key: {master_key[:10]}... (length: {len(master_key)})")
        
        try:
            self._fernet = Fernet(master_key.encode('utf-8'))
            logger.info("[CRYPTO] ✅ Initialized with master encryption key")
        except Exception as e:
            logger.error(f"[CRYPTO] ❌ Key validation failed: {e}")
            logger.error(f"[CRYPTO] Key must be 44 characters, got: {len(master_key)}")
            raise ValueError(f"Invalid MASTER_ENCRYPTION_KEY: {e}")
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        if not self._fernet:
            raise RuntimeError("CryptoService not initialized")
        try:
            encrypted_data = self._fernet.encrypt(data.encode('utf-8'))
            return encrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise RuntimeError("Encryption failed")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string"""
        if not self._fernet:
            raise RuntimeError("CryptoService not initialized")
        try:
            decrypted_data = self._fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except InvalidToken:
            logger.error("Decryption failed: Invalid token")
            raise RuntimeError("Decryption failed: Invalid token")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise RuntimeError("Decryption failed")
