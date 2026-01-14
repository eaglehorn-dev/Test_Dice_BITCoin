"""
Treasury Service
Secure withdrawal of funds from game wallets to cold storage
"""
import httpx
from typing import Dict, Any
from bitcoinlib.transactions import Transaction as BTCTransaction, Input, Output
from bitcoinlib.keys import Key
from loguru import logger
from app.core.config import admin_config
from app.services.wallet_service import WalletService

class TreasuryService:
    """Manages treasury operations and withdrawals"""
    
    def __init__(self):
        self.wallet_service = WalletService()
        self.network = admin_config.NETWORK
        self.mempool_api = admin_config.MEMPOOL_SPACE_API
        self.blockstream_api = admin_config.BLOCKSTREAM_API
        self.cold_storage = admin_config.COLD_STORAGE_ADDRESS
    
    async def get_wallet_balance(self, address: str) -> int:
        """Get wallet balance in satoshis from blockchain"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.mempool_api}/address/{address}", timeout=10)
                if response.status_code != 200:
                    response = await client.get(f"{self.blockstream_api}/address/{address}", timeout=10)
                
                response.raise_for_status()
                data = response.json()
                
                funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
                spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
                balance = funded - spent
                
                logger.info(f"[TREASURY] Balance for {address[:10]}...: {balance} sats")
                return balance
        
        except Exception as e:
            logger.error(f"[TREASURY] Failed to get balance for {address}: {e}")
            return 0
    
    async def get_utxos(self, address: str) -> list:
        """Fetch UTXOs for an address"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.mempool_api}/address/{address}/utxo", timeout=10)
                if response.status_code != 200:
                    response = await client.get(f"{self.blockstream_api}/address/{address}/utxo", timeout=10)
                
                response.raise_for_status()
                utxos = response.json()
                
                logger.info(f"[TREASURY] Found {len(utxos)} UTXOs for {address[:10]}...")
                return utxos
        
        except Exception as e:
            logger.error(f"[TREASURY] Failed to get UTXOs: {e}")
            return []
    
    async def withdraw_to_cold_storage(self, wallet_id: str, amount_sats: int = None) -> Dict[str, Any]:
        """
        Withdraw funds from a game wallet to cold storage
        If amount_sats is None, withdraws entire balance
        """
        try:
            wallet_info = await self.wallet_service.get_wallet_by_id(wallet_id)
            source_address = wallet_info["address"]
            
            if not self.cold_storage:
                raise ValueError("Cold storage address not configured")
            
            utxos = await self.get_utxos(source_address)
            if not utxos:
                raise ValueError(f"No UTXOs available for {source_address}")
            
            total_input = sum(utxo["value"] for utxo in utxos)
            
            if amount_sats is None:
                amount_sats = total_input
            
            if amount_sats > total_input:
                raise ValueError(f"Insufficient funds: requested {amount_sats}, available {total_input}")
            
            fee = admin_config.DEFAULT_TX_FEE_SATOSHIS
            amount_to_send = amount_sats - fee
            
            if amount_to_send <= 546:  # Dust limit
                raise ValueError(f"Amount too small after fee: {amount_to_send} sats")
            
            private_key_wif = await self.wallet_service.decrypt_wallet_key(wallet_id)
            key = Key(import_key=private_key_wif, network=self.network)
            
            inputs = []
            for utxo in utxos:
                inputs.append(Input(
                    prev_txid=utxo["txid"],
                    output_n=utxo["vout"],
                    value=utxo["value"],
                    address=source_address,
                    witness_type='segwit' if source_address.startswith('bc1') or source_address.startswith('tb1') else 'legacy'
                ))
            
            outputs = [Output(
                value=amount_to_send,
                address=self.cold_storage
            )]
            
            witness_type = 'segwit' if source_address.startswith('bc1') or source_address.startswith('tb1') else 'legacy'
            
            tx = BTCTransaction(
                inputs=inputs,
                outputs=outputs,
                network=self.network,
                witness_type=witness_type
            )
            
            tx.sign(keys=[key])
            raw_tx_hex = tx.raw_hex()
            
            txid = await self._broadcast_transaction(raw_tx_hex)
            
            logger.success(f"[TREASURY] Withdrawal successful! TXID: {txid}")
            logger.info(f"[TREASURY] Sent {amount_to_send} sats from {source_address[:10]}... to {self.cold_storage[:10]}...")
            
            return {
                "success": True,
                "txid": txid,
                "amount_sent": amount_to_send,
                "fee": fee,
                "from_address": source_address,
                "to_address": self.cold_storage
            }
        
        except Exception as e:
            logger.error(f"[TREASURY] Withdrawal failed: {e}")
            raise RuntimeError(f"Withdrawal failed: {e}")
    
    async def _broadcast_transaction(self, raw_tx_hex: str) -> str:
        """Broadcast transaction to Bitcoin network"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mempool_api}/tx",
                    content=raw_tx_hex,
                    timeout=15
                )
                
                if response.status_code != 200:
                    response = await client.post(
                        f"{self.blockstream_api}/tx",
                        content=raw_tx_hex,
                        timeout=15
                    )
                
                response.raise_for_status()
                txid = response.text.strip()
                
                logger.info(f"[TREASURY] Broadcast successful: {txid}")
                return txid
        
        except Exception as e:
            logger.error(f"[TREASURY] Broadcast failed: {e}")
            raise RuntimeError(f"Broadcast failed: {e}")
