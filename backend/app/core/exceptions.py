"""
Custom exceptions for the dice game application
Provides specific error types for better error handling
"""
from typing import Optional, Any, Dict


class DiceGameException(Exception):
    """Base exception for all dice game errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(DiceGameException):
    """Raised when database operations fail"""
    pass


class TransactionNotFoundException(DiceGameException):
    """Raised when a transaction is not found"""
    pass


class BetNotFoundException(DiceGameException):
    """Raised when a bet is not found"""
    pass


class InvalidBetException(DiceGameException):
    """Raised when bet parameters are invalid"""
    pass


class InsufficientFundsException(DiceGameException):
    """Raised when house wallet has insufficient funds for payout"""
    pass


class PayoutException(DiceGameException):
    """Raised when payout processing fails"""
    pass


class BlockchainException(DiceGameException):
    """Raised when blockchain/network operations fail"""
    pass


class WebSocketException(DiceGameException):
    """Raised when WebSocket operations fail"""
    pass


class ConfigurationException(DiceGameException):
    """Raised when configuration is invalid"""
    pass


class ProvablyFairException(DiceGameException):
    """Raised when provably fair calculations fail"""
    pass


class RateLimitException(DiceGameException):
    """Raised when rate limits are exceeded"""
    pass


class AuthenticationException(DiceGameException):
    """Raised when authentication fails"""
    pass


class ValidationException(DiceGameException):
    """Raised when input validation fails"""
    pass
