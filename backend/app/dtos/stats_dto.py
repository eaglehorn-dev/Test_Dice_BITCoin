"""
Statistics Data Transfer Objects
"""
from pydantic import BaseModel


class UserStatsResponse(BaseModel):
    """User statistics"""
    address: str
    total_bets: int
    total_wagered: int  # satoshis
    total_won: int
    total_lost: int
    net_profit: int  # total_won - total_lost
    win_rate: float  # percentage


class GameStatsResponse(BaseModel):
    """Overall game statistics"""
    total_bets: int
    total_users: int
    total_wagered: int
    total_paid_out: int
    house_profit: int
    active_bets: int
    pending_payouts: int


class TransactionStatsResponse(BaseModel):
    """Transaction statistics"""
    total_transactions: int
    total_deposits: int
    avg_deposit_size: int
    total_payouts: int
    avg_payout_size: int
