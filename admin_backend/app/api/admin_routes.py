"""
Admin API Routes
All routes protected by API key + IP whitelist
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from loguru import logger

from app.middleware.auth import verify_admin_access
from app.services.wallet_service import WalletService
from app.services.treasury_service import TreasuryService
from app.services.analytics_service import AnalyticsService
from app.services.price_service import PriceService
from app.dtos.admin_dtos import (
    GenerateWalletRequest, GenerateWalletResponse,
    WalletInfo, WithdrawRequest, WithdrawResponse,
    StatsResponse, DashboardResponse, MultiplierVolumeResponse, DailyStatsResponse
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/wallet/generate", response_model=GenerateWalletResponse)
async def generate_wallet(
    request: GenerateWalletRequest,
    authorized: bool = Depends(verify_admin_access)
):
    """Generate a new Bitcoin wallet for a specific multiplier"""
    try:
        wallet_service = WalletService()
        wallet = await wallet_service.generate_wallet(request.multiplier)
        return GenerateWalletResponse(**wallet)
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to generate wallet: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/wallets", response_model=List[WalletInfo])
async def get_all_wallets(
    include_balance: bool = Query(False, description="Fetch real-time balances from blockchain"),
    authorized: bool = Depends(verify_admin_access)
):
    """Get all wallets with optional real-time balance fetching"""
    try:
        wallet_service = WalletService()
        treasury_service = TreasuryService()
        price_service = PriceService()
        
        wallets = await wallet_service.get_all_wallets()
        
        if include_balance:
            for wallet in wallets:
                balance = await treasury_service.get_wallet_balance(wallet["address"])
                wallet["balance_sats"] = balance
                wallet["balance_usd"] = await price_service.satoshis_to_usd(balance)
        
        return [WalletInfo(**w) for w in wallets]
    
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to get wallets: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/treasury/withdraw", response_model=WithdrawResponse)
async def withdraw_to_cold_storage(
    request: WithdrawRequest,
    authorized: bool = Depends(verify_admin_access)
):
    """Withdraw funds from a wallet to cold storage"""
    try:
        treasury_service = TreasuryService()
        result = await treasury_service.withdraw_to_cold_storage(
            request.wallet_id,
            request.amount_sats
        )
        return WithdrawResponse(**result)
    
    except Exception as e:
        logger.error(f"[ADMIN API] Withdrawal failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/stats/{period}", response_model=StatsResponse)
async def get_stats(
    period: str = "today",
    authorized: bool = Depends(verify_admin_access)
):
    """Get income/outcome statistics for a period (today, week, month, year, all)"""
    try:
        analytics_service = AnalyticsService()
        stats = await analytics_service.get_income_outcome_stats(period)
        return StatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to get stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/volume", response_model=List[MultiplierVolumeResponse])
async def get_volume_by_multiplier(
    period: str = Query("all", description="Period: today, week, month, year, all"),
    authorized: bool = Depends(verify_admin_access)
):
    """Get bet volume grouped by multiplier"""
    try:
        analytics_service = AnalyticsService()
        volumes = await analytics_service.get_volume_by_multiplier(period)
        return [MultiplierVolumeResponse(**v) for v in volumes]
    
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to get volume: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/daily", response_model=List[DailyStatsResponse])
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
    authorized: bool = Depends(verify_admin_access)
):
    """Get daily statistics for the last N days"""
    try:
        analytics_service = AnalyticsService()
        daily_stats = await analytics_service.get_daily_stats(days)
        return [DailyStatsResponse(**d) for d in daily_stats]
    
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to get daily stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    authorized: bool = Depends(verify_admin_access)
):
    """Get complete dashboard data"""
    try:
        wallet_service = WalletService()
        treasury_service = TreasuryService()
        analytics_service = AnalyticsService()
        price_service = PriceService()
        
        wallets = await wallet_service.get_all_wallets()
        
        total_balance_sats = 0
        for wallet in wallets:
            balance = await treasury_service.get_wallet_balance(wallet["address"])
            wallet["balance_sats"] = balance
            wallet["balance_usd"] = await price_service.satoshis_to_usd(balance)
            total_balance_sats += balance
        
        btc_price = await price_service.get_btc_price_usd()
        treasury_balance_btc = await price_service.satoshis_to_btc(total_balance_sats)
        treasury_balance_usd = await price_service.satoshis_to_usd(total_balance_sats)
        
        today_stats = await analytics_service.get_income_outcome_stats("today")
        week_stats = await analytics_service.get_income_outcome_stats("week")
        month_stats = await analytics_service.get_income_outcome_stats("month")
        all_time_stats = await analytics_service.get_income_outcome_stats("all")
        
        volume_by_multiplier = await analytics_service.get_volume_by_multiplier("all")
        
        return DashboardResponse(
            treasury_balance_sats=total_balance_sats,
            treasury_balance_btc=treasury_balance_btc,
            treasury_balance_usd=treasury_balance_usd,
            btc_price_usd=btc_price,
            today_stats=StatsResponse(**today_stats),
            week_stats=StatsResponse(**week_stats),
            month_stats=StatsResponse(**month_stats),
            all_time_stats=StatsResponse(**all_time_stats),
            wallets=[WalletInfo(**w) for w in wallets],
            volume_by_multiplier=[MultiplierVolumeResponse(**v) for v in volume_by_multiplier]
        )
    
    except Exception as e:
        logger.error(f"[ADMIN API] Dashboard failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    return {"status": "healthy", "service": "admin-backend"}
