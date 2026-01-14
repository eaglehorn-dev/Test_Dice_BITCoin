"""
Data Transfer Objects (DTOs) for API validation
"""
from .bet_dto import (
    CreateBetRequest,
    BetResponse,
    BetHistoryItem,
    BetHistoryResponse,
    RecentBetsResponse
)
from .payout_dto import PayoutResponse, PayoutStatusResponse
from .stats_dto import UserStatsResponse, GameStatsResponse, TransactionStatsResponse
from .transaction_dto import TransactionResponse, ManualProcessRequest

__all__ = [
    "CreateBetRequest",
    "BetResponse",
    "BetHistoryItem",
    "BetHistoryResponse",
    "RecentBetsResponse",
    "PayoutResponse",
    "PayoutStatusResponse",
    "UserStatsResponse",
    "GameStatsResponse",
    "TransactionStatsResponse",
    "TransactionResponse",
    "ManualProcessRequest"
]
