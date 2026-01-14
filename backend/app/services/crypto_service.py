"""
Crypto Service - Envelope Encryption for Wallet Vault
Uses Fernet (AES-256) to encrypt/decrypt private keys
"""
from cryptography.fernet import Fernet
from loguru import logger
from typing import Optional

from app.core.config import config
from app.core.exceptions import DiceGameException


class CryptoService:
    """
    Handles encryption/decryption of sensitive data using envelope encryption.
    
    Security Model:
    - Master Key stored in environment variable (never in database)
    - Private keys encrypted before storage
    - Keys only decrypted in memory during transaction signing
    - No logging of decrypted keys
    """
    
    def __init__(self):
        """Initialize with master encryption key from environment"""
        if not config.MASTER_ENCRYPTION_KEY:
            raise DiceGameException("MASTER_ENCRYPTION_KEY not configured")
        
        try:
            self.cipher = Fernet(config.MASTER_ENCRYPTION_KEY.encode())
        except Exception as e:
            raise DiceGameException(f"Invalid MASTER_ENCRYPTION_KEY format: {e}")
    
    def encrypt_private_key(self, private_key: str) -> str:
        """
        Encrypt a Bitcoin private key using Fernet (AES-256)
        
        Args:
            private_key: WIF format private key
            
        Returns:
            Encrypted private key (base64 encoded)
        """
        try:
            encrypted_bytes = self.cipher.encrypt(private_key.encode())
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"[CRYPTO] Encryption failed: {type(e).__name__}")
            raise DiceGameException("Failed to encrypt private key")
    
    def decrypt_private_key(self, encrypted_key: str) -> str:
        """
        Decrypt a Bitcoin private key
        
        Args:
            encrypted_key: Base64 encoded encrypted key
            
        Returns:
            Decrypted WIF format private key
            
        Security:
        - Result stored in memory only
        - Never logged or persisted
        - Should be used immediately and discarded
        """
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_key.encode())
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"[CRYPTO] Decryption failed: {type(e).__name__}")
            raise DiceGameException("Failed to decrypt private key")
    
    def encrypt_data(self, data: str) -> str:
        """Generic encryption for any sensitive data"""
        try:
            encrypted_bytes = self.cipher.encrypt(data.encode())
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"[CRYPTO] Data encryption failed: {type(e).__name__}")
            raise DiceGameException("Failed to encrypt data")
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Generic decryption for any sensitive data"""
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"[CRYPTO] Data decryption failed: {type(e).__name__}")
            raise DiceGameException("Failed to decrypt data")
    
    @staticmethod
    def generate_master_key() -> str:
        """
        Generate a new master encryption key
        
        Usage:
            Add to .env file as MASTER_ENCRYPTION_KEY=<generated_key>
            
        Returns:
            Base64 encoded Fernet key
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')


def generate_encryption_key() -> str:
    """
    Utility function to generate a new master encryption key
    
    Run this once and add the result to your .env file:
    MASTER_ENCRYPTION_KEY=<generated_key>
    """
    return CryptoService.generate_master_key()
