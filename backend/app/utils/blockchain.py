"""
Blockchain utilities - Bitcoin transaction helpers
"""
import httpx
from typing import Optional, Dict, Any, List
from loguru import logger

from app.core.config import config
from app.core.exceptions import BlockchainException


class BlockchainHelper:
    """Helper class for blockchain operations"""
    
    @staticmethod
    async def get_transaction_details(txid: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from Mempool.space
        
        Args:
            txid: Transaction ID
            
        Returns:
            Transaction data or None
        """
        try:
            url = f"{config.MEMPOOL_SPACE_API}/tx/{txid}"
            
            async with httpx.AsyncClient(timeout=float(config.API_REQUEST_TIMEOUT)) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"[BLOCKCHAIN] Failed to get tx {txid}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"[BLOCKCHAIN] Error getting transaction: {e}")
            return None
    
    @staticmethod
    async def get_utxos(address: str) -> List[Dict[str, Any]]:
        """
        Get UTXOs for an address
        
        Args:
            address: Bitcoin address
            
        Returns:
            List of UTXOs
        """
        try:
            url = f"{config.MEMPOOL_SPACE_API}/address/{address}/utxo"
            
            async with httpx.AsyncClient(timeout=float(config.API_REQUEST_TIMEOUT)) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"[BLOCKCHAIN] Failed to get UTXOs for {address}: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"[BLOCKCHAIN] Error getting UTXOs: {e}")
            return []
    
    @staticmethod
    async def get_address_balance(address: str) -> int:
        """
        Get address balance in satoshis
        
        Args:
            address: Bitcoin address
            
        Returns:
            Balance in satoshis
        """
        try:
            utxos = await BlockchainHelper.get_utxos(address)
            return sum(utxo.get('value', 0) for utxo in utxos)
        except Exception as e:
            logger.error(f"[BLOCKCHAIN] Error getting balance: {e}")
            return 0
    
    @staticmethod
    async def broadcast_transaction(raw_tx_hex: str) -> Optional[str]:
        """
        Broadcast a raw transaction
        
        Args:
            raw_tx_hex: Raw transaction in hex format
            
        Returns:
            Transaction ID or None
        """
        try:
            # Try Mempool.space first
            url = f"{config.MEMPOOL_SPACE_API}/tx"
            
            async with httpx.AsyncClient(timeout=float(config.BROADCAST_TIMEOUT)) as client:
                response = await client.post(url, content=raw_tx_hex)
                
                if response.status_code == 200:
                    txid = response.text.strip()
                    logger.info(f"[BLOCKCHAIN] ✅ Broadcast successful: {txid[:16]}...")
                    return txid
                else:
                    logger.warning(f"[BLOCKCHAIN] Mempool.space broadcast failed: {response.status_code}")
            
            # Try Blockstream as backup
            url = f"{config.BLOCKSTREAM_API}/tx"
            
            async with httpx.AsyncClient(timeout=float(config.BROADCAST_TIMEOUT)) as client:
                response = await client.post(url, content=raw_tx_hex)
                
                if response.status_code == 200:
                    txid = response.text.strip()
                    logger.info(f"[BLOCKCHAIN] ✅ Broadcast successful via Blockstream: {txid[:16]}...")
                    return txid
                else:
                    logger.error(f"[BLOCKCHAIN] Blockstream broadcast failed: {response.status_code}")
            
            raise BlockchainException("All broadcast attempts failed")
            
        except Exception as e:
            logger.error(f"[BLOCKCHAIN] Error broadcasting transaction: {e}")
            raise BlockchainException(f"Failed to broadcast transaction: {str(e)}")
    
    @staticmethod
    def validate_bitcoin_address(address: str, network: str = "mainnet") -> bool:
        """
        Validate Bitcoin address format
        
        Args:
            address: Bitcoin address to validate
            network: Network type (mainnet/testnet)
            
        Returns:
            True if valid
        """
        try:
            if network == "mainnet":
                # Mainnet addresses
                if address.startswith('1') or address.startswith('3') or address.startswith('bc1'):
                    return len(address) >= 26 and len(address) <= 90
            else:
                # Testnet addresses
                if address.startswith('m') or address.startswith('n') or address.startswith('2') or address.startswith('tb1'):
                    return len(address) >= 26 and len(address) <= 90
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def is_segwit_address(address: str) -> bool:
        """Check if address is SegWit (bech32)"""
        return address.startswith('bc1') or address.startswith('tb1')
    
    @staticmethod
    def get_address_type(address: str) -> str:
        """Get address type (P2PKH, P2SH, P2WPKH, etc.)"""
        if address.startswith('1'):
            return "P2PKH"  # Legacy
        elif address.startswith('3'):
            return "P2SH"  # Script
        elif address.startswith('bc1'):
            return "P2WPKH"  # SegWit mainnet
        elif address.startswith('m') or address.startswith('n'):
            return "P2PKH"  # Testnet legacy
        elif address.startswith('2'):
            return "P2SH"  # Testnet script
        elif address.startswith('tb1'):
            return "P2WPKH"  # SegWit testnet
        else:
            return "Unknown"
