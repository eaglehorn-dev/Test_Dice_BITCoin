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
from app.services.server_seed_service import ServerSeedService
from app.dtos.admin_dtos import (
    GenerateWalletRequest, GenerateWalletResponse,
    WalletInfo, WithdrawRequest, WithdrawResponse,
    UpdateWalletRequest, UpdateWalletResponse, DeleteWalletResponse,
    StatsResponse, DashboardResponse, MultiplierVolumeResponse, DailyStatsResponse,
    CreateServerSeedRequest, CreateServerSeedResponse, ServerSeedInfo
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/wallet/generate", response_model=GenerateWalletResponse)
async def generate_wallet(
    request: GenerateWalletRequest,
    authorized: bool = Depends(verify_admin_access)
):
    """Generate a new Bitcoin wallet for a specific multiplier and address type"""
    try:
        wallet_service = WalletService()
        wallet = await wallet_service.generate_wallet(request.multiplier, request.address_type, request.chance)
        return GenerateWalletResponse(**wallet)
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to generate wallet: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/wallet/{wallet_id}", response_model=UpdateWalletResponse)
async def update_wallet(
    wallet_id: str,
    request: UpdateWalletRequest,
    authorized: bool = Depends(verify_admin_access)
):
    """Update wallet properties (multiplier, label, active status)"""
    try:
        wallet_service = WalletService()
        result = await wallet_service.update_wallet(
            wallet_id,
            multiplier=request.multiplier,
            chance=request.chance,
            label=request.label,
            is_active=request.is_active
        )
        return UpdateWalletResponse(**result)
    except ValueError as e:
        logger.error(f"[ADMIN API] Wallet update validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to update wallet: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/wallet/{wallet_id}", response_model=DeleteWalletResponse)
async def delete_wallet(
    wallet_id: str,
    authorized: bool = Depends(verify_admin_access)
):
    """Delete a wallet (WARNING: Permanent deletion including private key)"""
    try:
        wallet_service = WalletService()
        result = await wallet_service.delete_wallet(wallet_id)
        return DeleteWalletResponse(**result)
    except ValueError as e:
        logger.error(f"[ADMIN API] Wallet not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to delete wallet: {e}")
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
                usd_value = await price_service.satoshis_to_usd(balance)
                wallet["balance_usd"] = usd_value if usd_value is not None else 0.0
        
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
        
        # If no wallets, return empty dashboard quickly
        if not wallets or len(wallets) == 0:
            empty_stats = {
                "total_bets": 0,
                "total_income": 0,
                "total_payout": 0,
                "net_profit": 0,
                "total_wins": 0,
                "total_losses": 0,
                "win_rate": 0.0
            }
            
            return DashboardResponse(
                treasury_balance_sats=0,
                treasury_balance_btc=0.0,
                treasury_balance_usd=None,
                btc_price_usd=None,
                today_stats=StatsResponse(**empty_stats),
                week_stats=StatsResponse(**empty_stats),
                month_stats=StatsResponse(**empty_stats),
                all_time_stats=StatsResponse(**empty_stats),
                wallets=[],
                volume_by_multiplier=[],
                is_testnet=price_service.is_testnet
            )
        
        total_balance_sats = 0
        # Note: Fetching blockchain balances can be slow, using stored balance instead
        for wallet in wallets:
            # Use stored balance from database instead of fetching from blockchain
            wallet["balance_sats"] = wallet.get("balance_satoshis", 0)
            wallet["balance_usd"] = None  # Will calculate if needed
            total_balance_sats += wallet["balance_sats"]
        
        btc_price = await price_service.get_btc_price_usd()
        treasury_balance_btc = await price_service.satoshis_to_btc(total_balance_sats)
        treasury_balance_usd = await price_service.satoshis_to_usd(total_balance_sats)
        
        today_stats = await analytics_service.get_income_outcome_stats("today")
        week_stats = await analytics_service.get_income_outcome_stats("week")
        month_stats = await analytics_service.get_income_outcome_stats("month")
        all_time_stats = await analytics_service.get_income_outcome_stats("all")
        
        volume_by_multiplier = await analytics_service.get_volume_by_multiplier("all")
        
        is_testnet = price_service.is_testnet
        
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
            volume_by_multiplier=[MultiplierVolumeResponse(**v) for v in volume_by_multiplier],
            is_testnet=is_testnet
        )
    
    except Exception as e:
        logger.error(f"[ADMIN API] Dashboard failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    return {"status": "healthy", "service": "admin-backend"}

# Server Seed Management Routes
@router.get("/server-seeds", response_model=List[ServerSeedInfo])
async def get_all_server_seeds(
    authorized: bool = Depends(verify_admin_access)
):
    """Get all server seeds"""
    try:
        seed_service = ServerSeedService()
        seeds = await seed_service.get_all_seeds()
        
        return [
            ServerSeedInfo(
                seed_id=str(s["_id"]),
                server_seed_hash=s["server_seed_hash"],
                seed_date=s.get("seed_date", ""),
                created_at=s.get("created_at"),
                bet_count=s.get("bet_count", 0)
            )
            for s in seeds
        ]
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to get server seeds: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/server-seed/create", response_model=CreateServerSeedResponse)
async def create_server_seed(
    request: CreateServerSeedRequest,
    authorized: bool = Depends(verify_admin_access)
):
    """Create or update a server seed for a specific date"""
    try:
        seed_service = ServerSeedService()
        # Check if seed already exists
        existing = await seed_service.collection.find_one({"seed_date": request.seed_date})
        seed = await seed_service.create_server_seed(request.seed_date)
        
        message = "Server seed updated successfully" if existing else "Server seed created successfully"
        
        return CreateServerSeedResponse(
            seed_id=str(seed["_id"]),
            server_seed_hash=seed["server_seed_hash"],
            seed_date=seed["seed_date"],
            message=message
        )
    except ValueError as e:
        logger.error(f"[ADMIN API] Invalid date format: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to create server seed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/server-seed/{seed_id}")
async def delete_server_seed(
    seed_id: str,
    authorized: bool = Depends(verify_admin_access)
):
    """Delete a server seed (only future dates can be deleted)"""
    try:
        seed_service = ServerSeedService()
        success = await seed_service.delete_seed(seed_id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server seed not found")
        
        return {"success": True, "message": "Server seed deleted successfully"}
    except ValueError as e:
        logger.error(f"[ADMIN API] Cannot delete past date seed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN API] Failed to delete server seed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
