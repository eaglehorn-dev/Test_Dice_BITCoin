"""
Bitcoin Price Service
Fetches BTC/USD price from CoinGecko API (MAINNET ONLY)
"""
import httpx
from typing import Optional
from loguru import logger
from app.core.config import admin_config

class PriceService:
    """Service to fetch Bitcoin price in USD (mainnet only)"""
    
    def __init__(self):
        self.coingecko_url = admin_config.COINGECKO_API_URL
        self.is_testnet = admin_config.NETWORK == "testnet"
        self._cached_price = None
        self._cache_timestamp = 0
        self._cache_ttl = 60
    
    async def get_btc_price_usd(self) -> Optional[float]:
        """
        Get current BTC/USD price from CoinGecko
        Returns None for testnet (testnet BTC has no real value)
        """
        if self.is_testnet:
            logger.debug("[PRICE] Skipping USD fetch - testnet BTC has no value")
            return None
        
        import time
        current_time = time.time()
        
        if self._cached_price and (current_time - self._cache_timestamp) < self._cache_ttl:
            return self._cached_price
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.coingecko_url}/simple/price",
                    params={"ids": "bitcoin", "vs_currencies": "usd"},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                price = float(data["bitcoin"]["usd"])
                
                self._cached_price = price
                self._cache_timestamp = current_time
                
                logger.info(f"[PRICE] BTC/USD: ${price:,.2f}")
                return price
        
        except Exception as e:
            logger.error(f"[PRICE] Failed to fetch BTC price: {e}")
            if self._cached_price:
                logger.warning(f"[PRICE] Using cached price: ${self._cached_price:,.2f}")
                return self._cached_price
            return None
    
    async def satoshis_to_usd(self, satoshis: int) -> Optional[float]:
        """
        Convert satoshis to USD (mainnet only)
        Returns None for testnet
        """
        if self.is_testnet:
            return None
        
        btc_price = await self.get_btc_price_usd()
        if btc_price is None:
            return None
        
        btc_amount = satoshis / 100_000_000
        return btc_amount * btc_price
    
    async def satoshis_to_btc(self, satoshis: int) -> float:
        """Convert satoshis to BTC"""
        return satoshis / 100_000_000
