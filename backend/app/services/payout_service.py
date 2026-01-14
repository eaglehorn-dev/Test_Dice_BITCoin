"""
Payout Service - Business logic for Bitcoin payouts
Uses encrypted wallet vault for dynamic key management
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
import httpx
from loguru import logger

from app.core.config import config
from app.core.exceptions import InsufficientFundsException, PayoutException
from app.repository.payout_repository import PayoutRepository
from app.repository.bet_repository import BetRepository
from app.repository.transaction_repository import TransactionRepository
from app.repository.user_repository import UserRepository
from app.services.wallet_service import WalletService


class PayoutService:
    """Service for payout processing with encrypted wallet vault"""
    
    def __init__(self):
        self.payout_repo = PayoutRepository()
        self.bet_repo = BetRepository()
        self.tx_repo = TransactionRepository()
        self.user_repo = UserRepository()
        self.wallet_service = WalletService()
        
        self.network = config.NETWORK
        self.mempool_api = config.MEMPOOL_SPACE_API
        self.blockstream_api = config.BLOCKSTREAM_API
    
    async def process_winning_bet(self, bet_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a winning bet and create payout
        
        Args:
            bet_dict: Bet dictionary that won
            
        Returns:
            Payout dictionary or None if failed
        """
        try:
            # Verify bet is eligible for payout
            if not await self._is_eligible_for_payout(bet_dict):
                logger.warning(f"Bet {bet_dict['_id']} not eligible for payout")
                return None
            
            # Check if payout already exists
            existing_payout = await self.payout_repo.get_by_bet_id(bet_dict["_id"])
            
            if existing_payout:
                logger.info(f"Payout already exists for bet {bet_dict['_id']}")
                return existing_payout
            
            # Determine recipient address
            recipient_address = await self._get_recipient_address(bet_dict)
            
            if not recipient_address:
                logger.error(f"Cannot determine recipient address for bet {bet_dict['_id']}")
                return None
            
            # Create payout record
            payout_doc = {
                "bet_id": bet_dict["_id"],
                "amount": bet_dict["payout_amount"],
                "to_address": recipient_address,
                "status": "pending",
                "error_message": None,
                "network_fee": None,
                "retry_count": 0,
                "max_retries": 3,
                "txid": None,
                "created_at": datetime.utcnow(),
                "broadcast_at": None,
                "confirmed_at": None
            }
            
            payout_id = await self.payout_repo.insert_one(payout_doc)
            payout_doc["_id"] = payout_id
            
            logger.info(f"[OK] Created payout {payout_doc['_id']} for bet {bet_dict['_id']}: {payout_doc['amount']} sats to {recipient_address}")
            
            # Attempt to broadcast payout in background
            import asyncio
            asyncio.create_task(self._async_broadcast_and_update(payout_id, bet_dict["_id"]))
            
            return payout_doc
            
        except Exception as e:
            logger.error(f"Error processing winning bet {bet_dict['_id']}: {e}")
            return None
    
    async def _async_broadcast_and_update(self, payout_id: ObjectId, bet_id: ObjectId):
        """Async wrapper to broadcast payout and update bet status"""
        try:
            # Fetch objects from database
            payout = await self.payout_repo.find_by_id(payout_id)
            bet = await self.bet_repo.find_by_id(bet_id)
            
            if not payout or not bet:
                logger.error(f"Payout {payout_id} or Bet {bet_id} not found")
                return
            
            # Broadcast payout
            success = await self._broadcast_payout(payout)
            
            if success:
                await self.bet_repo.update_status(bet_id, "paid")
                logger.info(f"[OK] Bet {bet_id} marked as paid")
                
        except Exception as e:
            logger.error(f"Error in async broadcast wrapper: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _is_eligible_for_payout(self, bet_dict: Dict[str, Any]) -> bool:
        """Check if bet is eligible for payout"""
        
        # Must be a win
        if not bet_dict.get("is_win"):
            return False
        
        # Must have payout amount
        if not bet_dict.get("payout_amount") or bet_dict["payout_amount"] <= 0:
            return False
        
        # Must be confirmed
        if bet_dict.get("status") not in ["confirmed", "rolled"]:
            return False
        
        # Must not already be paid
        if bet_dict.get("status") == "paid":
            return False
        
        # Check transaction confirmations if required
        if config.MIN_CONFIRMATIONS_PAYOUT > 0:
            if bet_dict.get("deposit_txid"):
                tx = await self.tx_repo.get_by_txid(bet_dict["deposit_txid"])
                if tx and tx.get("confirmations", 0) < config.MIN_CONFIRMATIONS_PAYOUT:
                    logger.info(f"Bet {bet_dict['_id']} waiting for confirmations: {tx.get('confirmations', 0)}/{config.MIN_CONFIRMATIONS_PAYOUT}")
                    return False
        
        return True
    
    async def _get_recipient_address(self, bet_dict: Dict[str, Any]) -> Optional[str]:
        """Determine recipient address for payout"""
        # Try to get from transaction
        if bet_dict.get("deposit_txid"):
            tx = await self.tx_repo.get_by_txid(bet_dict["deposit_txid"])
            if tx and tx.get("from_address"):
                return tx["from_address"]
        
        # Try to get from user
        if bet_dict.get("user_id"):
            user = await self.user_repo.find_by_id(bet_dict["user_id"])
            if user and user.get("address"):
                return user["address"]
        
        return None
    
    async def _broadcast_payout(self, payout_dict: Dict[str, Any]) -> bool:
        """Broadcast payout transaction to network"""
        try:
            if payout_dict.get("retry_count", 0) >= payout_dict.get("max_retries", 3):
                logger.error(f"Payout {payout_dict['_id']} exceeded max retries")
                await self.payout_repo.update_status(
                    payout_dict["_id"],
                    "failed",
                    error_message="Max retries exceeded"
                )
                return False
            
            await self.payout_repo.increment_retry_count(payout_dict["_id"])
            
            logger.info(f"Broadcasting payout {payout_dict['_id']}: {payout_dict['amount']} sats to {payout_dict['to_address']}")
            
            bet = await self.bet_repo.find_by_id(payout_dict["bet_id"])
            if not bet:
                raise PayoutException("Bet not found for payout")
            
            result = await self._send_bitcoin(
                to_address=payout_dict["to_address"],
                amount_satoshis=payout_dict["amount"],
                bet_dict=bet
            )
            
            if result and result.get('tx', {}).get('hash'):
                txid = result['tx']['hash']
                
                update_data = {
                    "txid": txid,
                    "status": "broadcast",
                    "broadcast_at": datetime.utcnow()
                }
                
                # Extract fee if available
                if 'fees' in result['tx']:
                    update_data["network_fee"] = result['tx']['fees']
                
                await self.payout_repo.update_by_id(payout_dict["_id"], {"$set": update_data})
                
                logger.info(f"[OK] Payout {payout_dict['_id']} broadcast successfully: {txid}")
                return True
            
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                await self.payout_repo.update_by_id(
                    payout_dict["_id"],
                    {"$set": {"error_message": str(error_msg)}}
                )
                
                logger.error(f"❌ Failed to broadcast payout {payout_dict['_id']}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error broadcasting payout {payout_dict['_id']}: {e}")
            
            update_data = {"error_message": str(e)}
            
            if payout_dict.get("retry_count", 0) + 1 >= payout_dict.get("max_retries", 3):
                update_data["status"] = "failed"
            
            await self.payout_repo.update_by_id(payout_dict["_id"], {"$set": update_data})
            return False
    
    async def _get_utxos(self, address: str) -> List[Dict[str, Any]]:
        """Get UTXOs for an address from Mempool.space API"""
        try:
            url = f"{self.mempool_api}/address/{address}/utxo"
            
            async with httpx.AsyncClient(timeout=float(config.API_REQUEST_TIMEOUT)) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    utxos = response.json()
                    logger.info(f"[PAYOUT] Found {len(utxos)} UTXOs for {address[:10]}...")
                    return utxos
                else:
                    logger.warning(f"[PAYOUT] Mempool.space returned {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"[PAYOUT] Error fetching UTXOs: {e}")
            return []
    
    async def _broadcast_raw_tx(self, raw_tx_hex: str) -> Optional[str]:
        """Broadcast raw transaction hex to network"""
        try:
            # Try Mempool.space first
            url = f"{self.mempool_api}/tx"
            
            async with httpx.AsyncClient(timeout=float(config.BROADCAST_TIMEOUT)) as client:
                response = await client.post(url, content=raw_tx_hex)
                
                if response.status_code == 200:
                    txid = response.text.strip()
                    logger.info(f"[PAYOUT] ✅ Broadcast successful via Mempool.space: {txid[:16]}...")
                    return txid
                else:
                    logger.warning(f"[PAYOUT] Mempool.space broadcast failed: {response.status_code}")
            
            # Try Blockstream as backup
            url = f"{self.blockstream_api}/tx"
            
            async with httpx.AsyncClient(timeout=float(config.BROADCAST_TIMEOUT)) as client:
                response = await client.post(url, content=raw_tx_hex)
                
                if response.status_code == 200:
                    txid = response.text.strip()
                    logger.info(f"[PAYOUT] ✅ Broadcast successful via Blockstream: {txid[:16]}...")
                    return txid
                else:
                    logger.error(f"[PAYOUT] Blockstream broadcast failed: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.error(f"[PAYOUT] Error broadcasting transaction: {e}")
            return None
    
    async def _send_bitcoin(self, to_address: str, amount_satoshis: int, bet_dict: Dict[str, Any]) -> Optional[dict]:
        """
        Send Bitcoin using encrypted wallet vault
        
        Security:
        - Private key decrypted only in memory during signing
        - Key immediately discarded after use
        - Never logged or persisted
        """
        try:
            from bitcoinlib.keys import Key
            from bitcoinlib.transactions import Transaction as BTCTransaction, Input, Output
            
            logger.info(f"[PAYOUT] Creating transaction: {amount_satoshis} sats to {to_address[:10]}...")
            
            target_address = bet_dict.get("target_address")
            if not target_address:
                logger.error(f"[PAYOUT] No target_address in bet {bet_dict['_id']}")
                raise PayoutException("Bet missing target_address - cannot determine wallet")
            
            wallet = await self.wallet_service.get_wallet_by_address(target_address)
            if not wallet:
                logger.error(f"[PAYOUT] Wallet not found for address {target_address[:10]}...")
                raise PayoutException(f"Wallet not found for address {target_address}")
            
            logger.info(f"[PAYOUT] Using {wallet['multiplier']}x wallet: {wallet['address'][:10]}...")
            
            import asyncio
            await asyncio.sleep(3)
            logger.info(f"[PAYOUT] Waited 3s for UTXO index to update")
            
            utxos = await self._get_utxos(wallet['address'])
            
            if not utxos:
                logger.error(f"[PAYOUT] No UTXOs available for {wallet['address'][:10]}...")
                await self.wallet_service.mark_wallet_depleted(str(wallet['_id']), is_depleted=True)
                raise InsufficientFundsException("No UTXOs available")
            
            # Select UTXOs
            fee_buffer = config.FEE_BUFFER_SATOSHIS
            selected_utxo = None
            for utxo in utxos:
                if utxo['value'] >= amount_satoshis + fee_buffer:
                    selected_utxo = utxo
                    break
            
            if not selected_utxo:
                # Try combining UTXOs
                total = sum(u['value'] for u in utxos)
                if total >= amount_satoshis + fee_buffer:
                    logger.info(f"[PAYOUT] Using multiple UTXOs (total: {total} sats)")
                    selected_utxo = utxos
                else:
                    logger.error(f"[PAYOUT] Insufficient funds: need {amount_satoshis + fee_buffer}, have {total}")
                    raise InsufficientFundsException(f"Insufficient funds: need {amount_satoshis + fee_buffer}, have {total}")
            
            private_key_wif = self.wallet_service.decrypt_private_key(wallet)
            
            logger.info(f"[PAYOUT] 🔓 Decrypted wallet key (in memory only)")
            
            network = 'testnet' if self.network != 'mainnet' else 'bitcoin'
            key = Key(private_key_wif, network=network)
            
            del private_key_wif
            logger.info(f"[PAYOUT] 🔒 Discarded decrypted key from memory")
            
            fee = config.DEFAULT_TX_FEE_SATOSHIS
            
            witness_type = 'segwit' if wallet['address'].startswith('bc1') or wallet['address'].startswith('tb1') else 'legacy'
            
            inputs = []
            if isinstance(selected_utxo, list):
                for utxo in selected_utxo:
                    inputs.append(Input(
                        prev_txid=utxo['txid'],
                        output_n=utxo['vout'],
                        keys=key,
                        witness_type=witness_type,
                        network=network
                    ))
                total_input = sum(u['value'] for u in selected_utxo)
            else:
                inputs.append(Input(
                    prev_txid=selected_utxo['txid'],
                    output_n=selected_utxo['vout'],
                    keys=key,
                    witness_type=witness_type,
                    network=network
                ))
                total_input = selected_utxo['value']
            
            outputs = [
                Output(amount_satoshis, address=to_address, network=network)
            ]
            
            change = total_input - amount_satoshis - fee
            if change > config.DUST_LIMIT_SATOSHIS:
                outputs.append(Output(change, address=wallet['address'], network=network))
            
            tx = BTCTransaction(inputs=inputs, outputs=outputs, network=network, witness_type=witness_type)
            tx.sign()
            
            raw_tx = tx.raw_hex()
            
            logger.info(f"[PAYOUT] ✅ Transaction signed, size: {len(raw_tx)//2} bytes")
            
            await self.wallet_service.record_transaction(
                wallet_id=str(wallet['_id']),
                sent=amount_satoshis + fee
            )
            
            txid = await self._broadcast_raw_tx(raw_tx)
            
            if txid:
                logger.info(f"[PAYOUT] 🚀 Broadcast complete: {txid[:16]}...")
                return {
                    'tx': {
                        'hash': txid,
                        'tx_hex': raw_tx
                    }
                }
            else:
                return None
            
        except Exception as e:
            logger.error(f"[PAYOUT] Error sending Bitcoin: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise PayoutException(f"Failed to send Bitcoin: {str(e)}")
    
    async def retry_failed_payouts(self) -> int:
        """Retry all failed payouts that haven't exceeded max retries"""
        try:
            # Get pending/failed payouts
            failed_payouts = await self.payout_repo.get_failed_payouts()
            
            retried = 0
            
            for payout in failed_payouts:
                logger.info(f"Retrying payout {payout['_id']}")
                
                success = await self._broadcast_payout(payout)
                
                if success:
                    retried += 1
                    
                    # Update bet status
                    # Refresh payout to get latest txid
                    payout_updated = await self.payout_repo.find_by_id(payout["_id"])
                    if payout_updated and payout_updated.get("txid"):
                        await self.bet_repo.update_by_id(
                            payout["bet_id"],
                            {"$set": {
                                "status": "paid",
                                "paid_at": datetime.utcnow(),
                                "payout_txid": payout_updated["txid"]
                            }}
                        )
            
            if retried > 0:
                logger.info(f"[OK] Retried {retried} payout(s)")
            
            return retried
            
        except Exception as e:
            logger.error(f"Error retrying payouts: {e}")
            return 0
    
    async def check_payout_confirmations(self) -> int:
        """Check confirmations for broadcast payouts"""
        try:
            # Get broadcast payouts
            broadcast_payouts = await self.payout_repo.get_broadcast_payouts()
            
            confirmed = 0
            
            for payout in broadcast_payouts:
                try:
                    # Check transaction status via Mempool.space
                    url = f"{self.mempool_api}/tx/{payout['txid']}"
                    
                    async with httpx.AsyncClient(timeout=float(config.API_REQUEST_TIMEOUT)) as client:
                        response = await client.get(url)
                        
                        if response.status_code == 200:
                            tx_data = response.json()
                            status = tx_data.get('status', {})
                            
                            if status.get('confirmed'):
                                await self.payout_repo.update_status(
                                    payout["_id"],
                                    "confirmed"
                                )
                                confirmed += 1
                                
                                logger.info(f"[OK] Payout {payout['_id']} confirmed: {payout['txid']}")
                
                except Exception as e:
                    logger.error(f"Error checking payout {payout['_id']}: {e}")
            
            return confirmed
            
        except Exception as e:
            logger.error(f"Error checking payout confirmations: {e}")
            return 0
