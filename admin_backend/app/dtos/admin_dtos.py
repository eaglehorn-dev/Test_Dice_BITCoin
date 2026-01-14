"""
Data Transfer Objects for Admin API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GenerateWalletRequest(BaseModel):
    """Request to generate a new wallet"""
    multiplier: int = Field(..., gt=0, description="Multiplier for this wallet (e.g., 2 for 2x)")

class GenerateWalletResponse(BaseModel):
    """Response from wallet generation"""
    wallet_id: str
    address: str
    multiplier: int
    is_active: bool

class WalletInfo(BaseModel):
    """Wallet information (without private key)"""
    wallet_id: str
    multiplier: int
    address: str
    is_active: bool
    is_depleted: bool
    total_received: int
    total_sent: int
    bet_count: int
    balance_sats: Optional[int] = None
    balance_usd: Optional[float] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime

class WithdrawRequest(BaseModel):
    """Request to withdraw funds to cold storage"""
    wallet_id: str = Field(..., description="ID of wallet to withdraw from")
    amount_sats: Optional[int] = Field(None, description="Amount in satoshis (None = withdraw all)")

class WithdrawResponse(BaseModel):
    """Response from withdrawal"""
    success: bool
    txid: str
    amount_sent: int
    fee: int
    from_address: str
    to_address: str

class StatsResponse(BaseModel):
    """Statistics response"""
    total_bets: int
    total_income: int
    total_payout: int
    net_profit: int
    total_wins: int
    total_losses: int
    win_rate: float

class MultiplierVolumeResponse(BaseModel):
    """Bet volume by multiplier"""
    multiplier: int
    bet_count: int
    total_wagered: int
    total_paid_out: int
    wins: int
    profit: int

class DailyStatsResponse(BaseModel):
    """Daily statistics"""
    date: str
    bets: int
    income: int
    payout: int
    profit: int
    wins: int

class DashboardResponse(BaseModel):
    """Complete dashboard data"""
    treasury_balance_sats: int
    treasury_balance_btc: float
    treasury_balance_usd: Optional[float] = None
    btc_price_usd: Optional[float] = None
    today_stats: StatsResponse
    week_stats: StatsResponse
    month_stats: StatsResponse
    all_time_stats: StatsResponse
    wallets: List[WalletInfo]
    volume_by_multiplier: List[MultiplierVolumeResponse]
    is_testnet: bool = False