"""
Wallet API routes - Frontend wallet address lookup
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
from loguru import logger

from app.services.wallet_service import WalletService


router = APIRouter(prefix="/api/wallets", tags=["wallets"])


class WalletAddressResponse(BaseModel):
    """Public wallet information for frontend"""
    multiplier: int
    chance: float
    address: str
    label: str
    is_active: bool
    network: str


class MultipliersResponse(BaseModel):
    """Available multipliers"""
    multipliers: List[int]


@router.get("/multipliers", response_model=MultipliersResponse)
async def get_available_multipliers():
    """
    Get list of available multipliers
    
    Returns:
        List of active multipliers (e.g., [2, 3, 5, 10, 100])
        
    Usage:
        Frontend uses this to populate the slider/dropdown
    """
    try:
        wallet_service = WalletService()
        multipliers = await wallet_service.get_available_multipliers()
        
        return MultipliersResponse(multipliers=multipliers)
        
    except Exception as e:
        logger.error(f"Error getting multipliers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/address/{multiplier}", response_model=WalletAddressResponse)
async def get_wallet_address(multiplier: int):
    """
    Get wallet address for a specific multiplier
    
    Args:
        multiplier: Desired multiplier (e.g., 2, 3, 5)
        
    Returns:
        Bitcoin address and QR code data for frontend
        
    Usage:
        When user moves slider to 3x, frontend calls GET /api/wallets/address/3
        Response includes the BTC address to display and generate QR code
    """
    try:
        wallet_service = WalletService()
        wallet = await wallet_service.get_wallet_for_multiplier(multiplier)
        
        if not wallet:
            raise HTTPException(
                status_code=404,
                detail=f"No active wallet found for {multiplier}x multiplier"
            )
        
        # Get chance from wallet (with fallback for old wallets)
        chance = wallet.get("chance")
        if chance is None:
            # Calculate default chance for backward compatibility
            from app.services.provably_fair_service import ProvablyFairService
            chance = ProvablyFairService.calculate_win_chance(multiplier)
        
        return WalletAddressResponse(
            multiplier=wallet["multiplier"],
            chance=chance,
            address=wallet["address"],
            label=wallet.get("label", f"{multiplier}x Wallet"),
            is_active=wallet["is_active"],
            network=wallet["network"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet address for {multiplier}x: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=List[WalletAddressResponse])
async def get_all_wallets():
    """
    Get all active wallets
    
    Returns:
        List of all available wallets with their addresses
        
    Usage:
        Frontend can preload all wallet addresses on page load
        for instant slider updates without API calls
    """
    try:
        wallet_service = WalletService()
        wallets = await wallet_service.get_active_wallets()
        
        from app.services.provably_fair_service import ProvablyFairService
        
        return [
            WalletAddressResponse(
                multiplier=w["multiplier"],
                chance=w.get("chance") or ProvablyFairService.calculate_win_chance(w["multiplier"]),
                address=w["address"],
                label=w.get("label", f"{w['multiplier']}x Wallet"),
                is_active=w["is_active"],
                network=w["network"]
            )
            for w in wallets
        ]
        
    except Exception as e:
        logger.error(f"Error getting all wallets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
