"""
Payout Engine
Automatic payout processing for winning bets
Handles Bitcoin transaction creation and broadcasting
"""
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from bson import ObjectId
import httpx
from loguru import logger

from .config import config
from .database import (
    get_bets_collection,
    get_payouts_collection,
    get_transactions_collection,
    get_users_collection,
    get_seeds_collection,
    get_deposit_addresses_collection
)
from .provably_fair import ProvablyFair


class PayoutEngine:
    """Automated payout processing engine"""
    
    def __init__(self):
        self.house_private_key = config.HOUSE_PRIVATE_KEY
        self.house_address = config.HOUSE_ADDRESS
        self.network = config.NETWORK
        
        # API endpoints from config
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
            payouts_col = get_payouts_collection()
            existing_payout = await payouts_col.find_one({"bet_id": bet_dict["_id"]})
            
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
            
            result = await payouts_col.insert_one(payout_doc)
            payout_doc["_id"] = result.inserted_id
            
            logger.info(f"[OK] Created payout {payout_doc['_id']} for bet {bet_dict['_id']}: {payout_doc['amount']} sats to {recipient_address}")
            
            # Attempt to broadcast payout in background
            import asyncio
            payout_id = payout_doc["_id"]
            bet_id = bet_dict["_id"]
            asyncio.create_task(self._async_broadcast_and_update(payout_id, bet_id))
            
            return payout_doc
            
        except Exception as e:
            logger.error(f"Error processing winning bet {bet_dict['_id']}: {e}")
            return None
    
    async def _async_broadcast_and_update(self, payout_id: ObjectId, bet_id: ObjectId):
        """Async wrapper to broadcast payout and update bet status"""
        try:
            # Fetch objects from database
            payouts_col = get_payouts_collection()
            bets_col = get_bets_collection()
            
            payout = await payouts_col.find_one({"_id": payout_id})
            bet = await bets_col.find_one({"_id": bet_id})
            
            if not payout or not bet:
                logger.error(f"Payout {payout_id} or Bet {bet_id} not found")
                return
            
            # Broadcast payout
            success = await self._broadcast_payout(payout)
            
            if success:
                await bets_col.update_one(
                    {"_id": bet_id},
                    {"$set": {
                        "status": "paid",
                        "paid_at": datetime.utcnow()
                    }}
                )
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
                txs_col = get_transactions_collection()
                tx = await txs_col.find_one({"txid": bet_dict["deposit_txid"]})
                if tx and tx.get("confirmations", 0) < config.MIN_CONFIRMATIONS_PAYOUT:
                    logger.info(f"Bet {bet_dict['_id']} waiting for confirmations: {tx.get('confirmations', 0)}/{config.MIN_CONFIRMATIONS_PAYOUT}")
                    return False
        
        return True
    
    async def _get_recipient_address(self, bet_dict: Dict[str, Any]) -> Optional[str]:
        """
        Determine recipient address for payout
        
        Priority:
        1. Sender address from transaction
        2. User's primary address
        
        Args:
            bet_dict: Bet dictionary
            
        Returns:
            Bitcoin address or None
        """
        # Try to get from transaction
        if bet_dict.get("deposit_txid"):
            txs_col = get_transactions_collection()
            tx = await txs_col.find_one({"txid": bet_dict["deposit_txid"]})
            if tx and tx.get("from_address"):
                return tx["from_address"]
        
        # Try to get from user
        if bet_dict.get("user_id"):
            users_col = get_users_collection()
            user = await users_col.find_one({"_id": bet_dict["user_id"]})
            if user and user.get("address"):
                return user["address"]
        
        return None
    
    async def _broadcast_payout(self, payout_dict: Dict[str, Any]) -> bool:
        """
        Broadcast payout transaction to network
        
        Args:
            payout_dict: Payout dictionary
            
        Returns:
            True if successful
        """
        try:
            payouts_col = get_payouts_collection()
            
            if payout_dict.get("retry_count", 0) >= payout_dict.get("max_retries", 3):
                logger.error(f"Payout {payout_dict['_id']} exceeded max retries")
                await payouts_col.update_one(
                    {"_id": payout_dict["_id"]},
                    {"$set": {
                        "status": "failed",
                        "error_message": "Max retries exceeded"
                    }}
                )
                return False
            
            await payouts_col.update_one(
                {"_id": payout_dict["_id"]},
                {"$inc": {"retry_count": 1}}
            )
            
            # Send Bitcoin transaction using bitcoinlib
            logger.info(f"Broadcasting payout {payout_dict['_id']}: {payout_dict['amount']} sats to {payout_dict['to_address']}")
            
            result = await self._send_bitcoin(
                to_address=payout_dict["to_address"],
                amount_satoshis=payout_dict["amount"],
                from_private_key=self.house_private_key
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
                
                await payouts_col.update_one(
                    {"_id": payout_dict["_id"]},
                    {"$set": update_data}
                )
                
                logger.info(f"[OK] Payout {payout_dict['_id']} broadcast successfully: {txid}")
                return True
            
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                await payouts_col.update_one(
                    {"_id": payout_dict["_id"]},
                    {"$set": {"error_message": str(error_msg)}}
                )
                
                logger.error(f"❌ Failed to broadcast payout {payout_dict['_id']}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error broadcasting payout {payout_dict['_id']}: {e}")
            
            payouts_col = get_payouts_collection()
            update_data = {"error_message": str(e)}
            
            if payout_dict.get("retry_count", 0) + 1 >= payout_dict.get("max_retries", 3):
                update_data["status"] = "failed"
            
            await payouts_col.update_one(
                {"_id": payout_dict["_id"]},
                {"$set": update_data}
            )
            return False
    
    async def _get_utxos(self, address: str) -> List[Dict[str, Any]]:
        """
        Get UTXOs for an address from Mempool.space API
        
        Args:
            address: Bitcoin address
            
        Returns:
            List of UTXO dictionaries
        """
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
        """
        Broadcast raw transaction hex to network
        
        Args:
            raw_tx_hex: Raw transaction in hex format
            
        Returns:
            Transaction ID or None
        """
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
    
    async def _send_bitcoin(self, to_address: str, amount_satoshis: int, from_private_key: str) -> Optional[dict]:
        """
        Send Bitcoin using bitcoinlib
        
        Args:
            to_address: Recipient address
            amount_satoshis: Amount to send in satoshis
            from_private_key: Sender's private key (WIF format)
            
        Returns:
            Transaction result dictionary or None
        """
        try:
            from bitcoinlib.keys import Key
            from bitcoinlib.transactions import Transaction as BTCTransaction, Input, Output
            
            logger.info(f"[PAYOUT] Creating transaction: {amount_satoshis} sats to {to_address[:10]}...")
            
            # Wait briefly for UTXO index to update (race condition fix)
            import asyncio
            await asyncio.sleep(3)
            logger.info(f"[PAYOUT] Waited 3s for UTXO index to update")
            
            # Get UTXOs for house address
            utxos = await self._get_utxos(self.house_address)
            
            if not utxos:
                logger.error(f"[PAYOUT] No UTXOs available for {self.house_address}")
                return None
            
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
                    return None
            
            # Create key from private key
            network = 'testnet' if self.network != 'mainnet' else 'bitcoin'
            key = Key(from_private_key, network=network)
            
            # Calculate transaction fee
            fee = config.DEFAULT_TX_FEE_SATOSHIS
            
            # Create transaction inputs (SegWit-aware)
            witness_type = 'segwit' if self.house_address.startswith('bc1') or self.house_address.startswith('tb1') else 'legacy'
            
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
            
            # Create transaction outputs
            outputs = [
                Output(amount_satoshis, address=to_address, network=network)
            ]
            
            # Add change output if needed
            change = total_input - amount_satoshis - fee
            if change > config.DUST_LIMIT_SATOSHIS:
                outputs.append(Output(change, address=self.house_address, network=network))
            
            # Create and sign transaction
            tx = BTCTransaction(inputs=inputs, outputs=outputs, network=network, witness_type=witness_type)
            tx.sign()
            
            # Get raw transaction hex
            raw_tx = tx.raw_hex()
            
            logger.info(f"[PAYOUT] Transaction signed, size: {len(raw_tx)//2} bytes")
            
            # Broadcast transaction
            txid = await self._broadcast_raw_tx(raw_tx)
            
            if txid:
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
            return None
    
    async def retry_failed_payouts(self) -> int:
        """
        Retry all failed payouts that haven't exceeded max retries
        
        Returns:
            Number of payouts retried
        """
        try:
            payouts_col = get_payouts_collection()
            bets_col = get_bets_collection()
            
            # Get pending/failed payouts
            failed_payouts = await payouts_col.find({
                "status": {"$in": ["pending", "failed"]},
                "$expr": {"$lt": ["$retry_count", "$max_retries"]}
            }).to_list(length=100)
            
            retried = 0
            
            for payout in failed_payouts:
                logger.info(f"Retrying payout {payout['_id']}")
                
                success = await self._broadcast_payout(payout)
                
                if success:
                    retried += 1
                    
                    # Update bet status
                    # Refresh payout to get latest txid
                    payout_updated = await payouts_col.find_one({"_id": payout["_id"]})
                    if payout_updated and payout_updated.get("txid"):
                        await bets_col.update_one(
                            {"_id": payout["bet_id"]},
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
    
    async def check_payout_confirmations_async(self) -> int:
        """
        Check confirmations for broadcast payouts using Mempool.space API
        
        Returns:
            Number of payouts confirmed
        """
        try:
            payouts_col = get_payouts_collection()
            
            # Get broadcast payouts
            broadcast_payouts = await payouts_col.find({
                "status": "broadcast",
                "txid": {"$ne": None, "$exists": True}
            }).to_list(length=100)
            
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
                                await payouts_col.update_one(
                                    {"_id": payout["_id"]},
                                    {"$set": {
                                        "status": "confirmed",
                                        "confirmed_at": datetime.utcnow()
                                    }}
                                )
                                confirmed += 1
                                
                                logger.info(f"[OK] Payout {payout['_id']} confirmed: {payout['txid']}")
                
                except Exception as e:
                    logger.error(f"Error checking payout {payout['_id']}: {e}")
            
            return confirmed
            
        except Exception as e:
            logger.error(f"Error checking payout confirmations: {e}")
            return 0
    
    def check_payout_confirmations(self) -> int:
        """Sync wrapper for check_payout_confirmations_async"""
        import asyncio
        return asyncio.run(self.check_payout_confirmations_async())


class BetProcessor:
    """Process bets through the complete lifecycle"""
    
    def __init__(self):
        self.payout_engine = PayoutEngine()
    
    async def process_detected_transaction(self, transaction_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a detected transaction into a bet
        
        Args:
            transaction_dict: Detected transaction dictionary
            
        Returns:
            Bet dictionary or None
        """
        try:
            bets_col = get_bets_collection()
            txs_col = get_transactions_collection()
            users_col = get_users_collection()
            deposit_addrs_col = get_deposit_addresses_collection()
            seeds_col = get_seeds_collection()
            
            # Check if bet already exists
            existing_bet = await bets_col.find_one({"deposit_txid": transaction_dict["txid"]})
            
            if existing_bet:
                logger.info(f"Bet already exists for transaction {transaction_dict['txid']}")
                # Mark transaction as processed if not already
                if not transaction_dict.get("is_processed"):
                    await txs_col.update_one(
                        {"_id": transaction_dict["_id"]},
                        {"$set": {
                            "is_processed": True,
                            "processed_at": datetime.utcnow()
                        }}
                    )
                return existing_bet
            
            # Check if already processed
            if transaction_dict.get("is_processed"):
                logger.warning(f"Transaction {transaction_dict['txid']} marked as processed but no bet found")
                return None
            
            # Get or create user
            user = await users_col.find_one({"address": transaction_dict["from_address"]})
            
            if not user:
                user_doc = {
                    "address": transaction_dict["from_address"],
                    "created_at": datetime.utcnow(),
                    "last_seen": datetime.utcnow(),
                    "total_bets": 0,
                    "total_wagered": 0,
                    "total_won": 0,
                    "total_lost": 0
                }
                result = await users_col.insert_one(user_doc)
                user_doc["_id"] = result.inserted_id
                user = user_doc
            
            # Get deposit address info for bet parameters
            deposit_addr = await deposit_addrs_col.find_one({"address": transaction_dict["to_address"]})
            
            # Determine multiplier
            multiplier = deposit_addr.get("expected_multiplier", 2.0) if deposit_addr else 2.0
            
            # Get or create active seed for user
            seed = await seeds_col.find_one({"user_id": user["_id"], "is_active": True})
            
            if not seed:
                from .provably_fair import generate_new_seed_pair
                
                server_seed, server_seed_hash, client_seed = generate_new_seed_pair(user["address"])
                
                seed_doc = {
                    "user_id": user["_id"],
                    "server_seed": server_seed,
                    "server_seed_hash": server_seed_hash,
                    "client_seed": client_seed,
                    "nonce": 0,
                    "is_active": True,
                    "revealed_at": None,
                    "created_at": datetime.utcnow()
                }
                result = await seeds_col.insert_one(seed_doc)
                seed_doc["_id"] = result.inserted_id
                seed = seed_doc
            
            # Validate bet parameters
            is_valid, error = ProvablyFair.validate_bet_params(transaction_dict["amount"], multiplier)
            
            if not is_valid:
                logger.error(f"Invalid bet parameters: {error}")
                await txs_col.update_one(
                    {"_id": transaction_dict["_id"]},
                    {"$set": {
                        "is_processed": True,
                        "processed_at": datetime.utcnow()
                    }}
                )
                return None
            
            # Calculate win chance
            win_chance = ProvablyFair.calculate_win_chance(multiplier)
            
            # Create bet
            bet_doc = {
                "user_id": user["_id"],
                "seed_id": seed["_id"],
                "bet_amount": transaction_dict["amount"],
                "target_multiplier": multiplier,
                "win_chance": win_chance,
                "nonce": seed["nonce"],
                "roll_result": None,
                "is_win": None,
                "payout_amount": None,
                "profit": None,
                "deposit_txid": transaction_dict["txid"],
                "deposit_address": transaction_dict["to_address"],
                "payout_txid": None,
                "status": "pending",
                "created_at": datetime.utcnow(),
                "confirmed_at": None,
                "rolled_at": None,
                "paid_at": None
            }
            
            result = await bets_col.insert_one(bet_doc)
            bet_doc["_id"] = result.inserted_id
            
            # Link transaction to bet
            await txs_col.update_one(
                {"_id": transaction_dict["_id"]},
                {"$set": {
                    "bet_id": bet_doc["_id"],
                    "is_processed": True,
                    "processed_at": datetime.utcnow()
                }}
            )
            
            # Mark deposit address as used
            if deposit_addr:
                await deposit_addrs_col.update_one(
                    {"_id": deposit_addr["_id"]},
                    {"$set": {
                        "is_used": True,
                        "used_at": datetime.utcnow()
                    }}
                )
            
            logger.info(f"[OK] Created bet {bet_doc['_id']} from transaction {transaction_dict['txid']}")
            
            # Check if should roll immediately
            if transaction_dict.get("confirmations", 0) >= config.MIN_CONFIRMATIONS_PAYOUT:
                await self.roll_and_payout_bet(bet_doc)
            
            return bet_doc
            
        except Exception as e:
            logger.error(f"Error processing transaction {transaction_dict['txid']}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def roll_and_payout_bet(self, bet_dict: Dict[str, Any]) -> bool:
        """
        Roll dice and process payout for a bet
        
        Args:
            bet_dict: Bet dictionary
            
        Returns:
            True if successful
        """
        try:
            bets_col = get_bets_collection()
            seeds_col = get_seeds_collection()
            users_col = get_users_collection()
            
            # Check if already rolled
            if bet_dict.get("roll_result") is not None:
                logger.info(f"Bet {bet_dict['_id']} already rolled")
                return True
            
            # Get seed
            seed = await seeds_col.find_one({"_id": bet_dict["seed_id"]})
            
            if not seed:
                logger.error(f"Seed not found for bet {bet_dict['_id']}")
                return False
            
            # Roll the dice
            result = ProvablyFair.create_bet_result(
                server_seed=seed["server_seed"],
                client_seed=seed["client_seed"],
                nonce=bet_dict["nonce"],
                bet_amount=bet_dict["bet_amount"],
                multiplier=bet_dict["target_multiplier"]
            )
            
            # Update bet with result
            await bets_col.update_one(
                {"_id": bet_dict["_id"]},
                {"$set": {
                    "roll_result": result["roll"],
                    "is_win": result["is_win"],
                    "payout_amount": result["payout"],
                    "profit": result["profit"],
                    "rolled_at": datetime.utcnow(),
                    "status": "rolled"
                }}
            )
            
            # Increment seed nonce
            await seeds_col.update_one(
                {"_id": seed["_id"]},
                {"$inc": {"nonce": 1}}
            )
            
            # Update user statistics
            update_stats = {
                "total_bets": 1,
                "total_wagered": bet_dict["bet_amount"]
            }
            
            if result["is_win"]:
                update_stats["total_won"] = result["profit"]
            else:
                update_stats["total_lost"] = abs(result["profit"])
            
            await users_col.update_one(
                {"_id": bet_dict["user_id"]},
                {"$inc": update_stats}
            )
            
            logger.info(f"[DICE] Bet {bet_dict['_id']} rolled: {result['roll']} ({'WIN' if result['is_win'] else 'LOSE'}) profit={result['profit']}")
            
            # Update bet_dict for payout
            bet_dict["roll_result"] = result["roll"]
            bet_dict["is_win"] = result["is_win"]
            bet_dict["payout_amount"] = result["payout"]
            bet_dict["profit"] = result["profit"]
            bet_dict["status"] = "rolled"
            
            # Process payout if winner
            if result["is_win"] and result["payout"] > 0:
                payout = await self.payout_engine.process_winning_bet(bet_dict)
                
                if payout and payout.get("txid"):
                    await bets_col.update_one(
                        {"_id": bet_dict["_id"]},
                        {"$set": {"payout_txid": payout["txid"]}}
                    )
            else:
                # Mark as paid (house keeps it)
                await bets_col.update_one(
                    {"_id": bet_dict["_id"]},
                    {"$set": {
                        "status": "paid",
                        "paid_at": datetime.utcnow()
                    }}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error rolling bet {bet_dict['_id']}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def process_pending_bets(self) -> int:
        """
        Process all pending bets that have sufficient confirmations
        
        Returns:
            Number of bets processed
        """
        try:
            bets_col = get_bets_collection()
            txs_col = get_transactions_collection()
            
            # Get pending/confirmed bets
            pending_bets = await bets_col.find({
                "status": {"$in": ["pending", "confirmed"]},
                "roll_result": None
            }).to_list(length=100)
            
            processed = 0
            
            for bet in pending_bets:
                # Check confirmations
                if bet.get("deposit_txid"):
                    tx = await txs_col.find_one({"txid": bet["deposit_txid"]})
                    if tx and tx.get("confirmations", 0) >= config.MIN_CONFIRMATIONS_PAYOUT:
                        await bets_col.update_one(
                            {"_id": bet["_id"]},
                            {"$set": {
                                "status": "confirmed",
                                "confirmed_at": datetime.utcnow()
                            }}
                        )
                        
                        # Roll and payout
                        if await self.roll_and_payout_bet(bet):
                            processed += 1
            
            if processed > 0:
                logger.info(f"[OK] Processed {processed} bet(s)")
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing pending bets: {e}")
            return 0
