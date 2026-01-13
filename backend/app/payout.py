"""
Payout Engine
Automatic payout processing for winning bets
Handles Bitcoin transaction creation and broadcasting
"""
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import httpx
from loguru import logger

from .config import config
from .database import Bet, Payout, Transaction
from .provably_fair import ProvablyFair


class PayoutEngine:
    """Automated payout processing engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.house_private_key = config.HOUSE_PRIVATE_KEY
        self.house_address = config.HOUSE_ADDRESS
        self.network = config.NETWORK
        
        # Set API endpoints based on network
        if self.network == 'mainnet':
            self.mempool_api = 'https://mempool.space/api'
            self.blockstream_api = 'https://blockstream.info/api'
        else:
            self.mempool_api = 'https://mempool.space/testnet/api'
            self.blockstream_api = 'https://blockstream.info/testnet/api'
    
    def process_winning_bet(self, bet: Bet) -> Optional[Payout]:
        """
        Process a winning bet and create payout
        
        Args:
            bet: Bet object that won
            
        Returns:
            Payout object or None if failed
        """
        try:
            # Verify bet is eligible for payout
            if not self._is_eligible_for_payout(bet):
                logger.warning(f"Bet {bet.id} not eligible for payout")
                return None
            
            # Check if payout already exists
            existing_payout = self.db.query(Payout).filter(
                Payout.bet_id == bet.id
            ).first()
            
            if existing_payout:
                logger.info(f"Payout already exists for bet {bet.id}")
                return existing_payout
            
            # Determine recipient address
            recipient_address = self._get_recipient_address(bet)
            
            if not recipient_address:
                logger.error(f"Cannot determine recipient address for bet {bet.id}")
                return None
            
            # Create payout record
            payout = Payout(
                bet_id=bet.id,
                amount=bet.payout_amount,
                to_address=recipient_address,
                status='pending'
            )
            
            self.db.add(payout)
            self.db.commit()
            self.db.refresh(payout)
            
            logger.info(f"[OK] Created payout {payout.id} for bet {bet.id}: {payout.amount} sats to {recipient_address}")
            
            # Attempt to broadcast payout
            # Note: Broadcasting is now async and will be handled in background
            import asyncio
            asyncio.create_task(self._async_broadcast_and_update(payout, bet))
            
            return payout
            
        except Exception as e:
            logger.error(f"Error processing winning bet {bet.id}: {e}")
            self.db.rollback()
            return None
    
    async def _async_broadcast_and_update(self, payout: Payout, bet: Bet):
        """Async wrapper to broadcast payout and update bet status"""
        try:
            success = await self._broadcast_payout(payout)
            
            if success:
                bet.status = 'paid'
                bet.paid_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"[OK] Bet {bet.id} marked as paid")
        except Exception as e:
            logger.error(f"Error in async broadcast wrapper: {e}")
    
    def _is_eligible_for_payout(self, bet: Bet) -> bool:
        """Check if bet is eligible for payout"""
        
        # Must be a win
        if not bet.is_win:
            return False
        
        # Must have payout amount
        if not bet.payout_amount or bet.payout_amount <= 0:
            return False
        
        # Must be confirmed
        if bet.status not in ['confirmed', 'rolled']:
            return False
        
        # Must not already be paid
        if bet.status == 'paid':
            return False
        
        # Check transaction confirmations if required
        if config.MIN_CONFIRMATIONS_PAYOUT > 0:
            if bet.transaction:
                if bet.transaction.confirmations < config.MIN_CONFIRMATIONS_PAYOUT:
                    logger.info(f"Bet {bet.id} waiting for confirmations: {bet.transaction.confirmations}/{config.MIN_CONFIRMATIONS_PAYOUT}")
                    return False
        
        return True
    
    def _get_recipient_address(self, bet: Bet) -> Optional[str]:
        """
        Determine recipient address for payout
        
        Priority:
        1. Sender address from transaction
        2. User's primary address
        
        Args:
            bet: Bet object
            
        Returns:
            Bitcoin address or None
        """
        # Try to get from transaction
        if bet.transaction and bet.transaction.from_address:
            return bet.transaction.from_address
        
        # Try to get from user
        if bet.user and bet.user.address:
            return bet.user.address
        
        return None
    
    async def _broadcast_payout(self, payout: Payout) -> bool:
        """
        Broadcast payout transaction to network
        
        Args:
            payout: Payout object
            
        Returns:
            True if successful
        """
        try:
            if payout.retry_count >= payout.max_retries:
                logger.error(f"Payout {payout.id} exceeded max retries")
                payout.status = 'failed'
                payout.error_message = "Max retries exceeded"
                self.db.commit()
                return False
            
            payout.retry_count += 1
            
            # Send Bitcoin transaction using bitcoinlib
            logger.info(f"Broadcasting payout {payout.id}: {payout.amount} sats to {payout.to_address}")
            
            # Call async function directly
            result = await self._send_bitcoin(
                to_address=payout.to_address,
                amount_satoshis=payout.amount,
                from_private_key=self.house_private_key
            )
            
            if result and result.get('tx', {}).get('hash'):
                txid = result['tx']['hash']
                payout.txid = txid
                payout.status = 'broadcast'
                payout.broadcast_at = datetime.utcnow()
                
                # Extract fee if available
                if 'fees' in result['tx']:
                    payout.network_fee = result['tx']['fees']
                
                self.db.commit()
                
                logger.info(f"[OK] Payout {payout.id} broadcast successfully: {txid}")
                return True
            
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                payout.error_message = str(error_msg)
                self.db.commit()
                
                logger.error(f"❌ Failed to broadcast payout {payout.id}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error broadcasting payout {payout.id}: {e}")
            payout.error_message = str(e)
            
            if payout.retry_count >= payout.max_retries:
                payout.status = 'failed'
            
            self.db.commit()
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
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
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, content=raw_tx_hex)
                
                if response.status_code == 200:
                    txid = response.text.strip()
                    logger.info(f"[PAYOUT] ✅ Broadcast successful via Mempool.space: {txid[:16]}...")
                    return txid
                else:
                    logger.warning(f"[PAYOUT] Mempool.space broadcast failed: {response.status_code}")
            
            # Try Blockstream as backup
            url = f"{self.blockstream_api}/tx"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
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
            
            # Get UTXOs for house address
            utxos = await self._get_utxos(self.house_address)
            
            if not utxos:
                logger.error(f"[PAYOUT] No UTXOs available for {self.house_address}")
                return None
            
            # Select UTXOs (simple: use first UTXO that's large enough)
            selected_utxo = None
            for utxo in utxos:
                if utxo['value'] >= amount_satoshis + 1000:  # +1000 for fee
                    selected_utxo = utxo
                    break
            
            if not selected_utxo:
                # Try combining UTXOs if single one isn't enough
                total = sum(u['value'] for u in utxos)
                if total >= amount_satoshis + 1000:
                    logger.info(f"[PAYOUT] Using multiple UTXOs (total: {total} sats)")
                    selected_utxo = utxos  # Use all
                else:
                    logger.error(f"[PAYOUT] Insufficient funds: need {amount_satoshis + 1000}, have {total}")
                    return None
            
            # Create key from private key
            network = 'testnet' if self.network != 'mainnet' else 'bitcoin'
            key = Key(from_private_key, network=network)
            
            # Calculate fee (simple: 1 sat/vbyte, ~250 bytes for typical tx)
            fee = 250
            
            # Create transaction inputs
            inputs = []
            if isinstance(selected_utxo, list):
                for utxo in selected_utxo:
                    inputs.append(Input(
                        prev_txid=utxo['txid'],
                        output_n=utxo['vout'],
                        keys=key,
                        network=network
                    ))
                total_input = sum(u['value'] for u in selected_utxo)
            else:
                inputs.append(Input(
                    prev_txid=selected_utxo['txid'],
                    output_n=selected_utxo['vout'],
                    keys=key,
                    network=network
                ))
                total_input = selected_utxo['value']
            
            # Create transaction outputs
            outputs = [
                Output(amount_satoshis, address=to_address, network=network)
            ]
            
            # Add change output if needed
            change = total_input - amount_satoshis - fee
            if change > 546:  # Dust limit
                outputs.append(Output(change, address=self.house_address, network=network))
            
            # Create and sign transaction
            tx = BTCTransaction(inputs=inputs, outputs=outputs, network=network)
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
            # Get pending/failed payouts
            failed_payouts = self.db.query(Payout).filter(
                Payout.status.in_(['pending', 'failed']),
                Payout.retry_count < Payout.max_retries
            ).all()
            
            retried = 0
            
            for payout in failed_payouts:
                logger.info(f"Retrying payout {payout.id}")
                
                success = await self._broadcast_payout(payout)
                
                if success:
                    retried += 1
                    
                    # Update bet status
                    bet = self.db.query(Bet).filter(Bet.id == payout.bet_id).first()
                    if bet:
                        bet.status = 'paid'
                        bet.paid_at = datetime.utcnow()
                        bet.payout_txid = payout.txid
            
            self.db.commit()
            
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
            # Get broadcast payouts
            broadcast_payouts = self.db.query(Payout).filter(
                Payout.status == 'broadcast',
                Payout.txid.isnot(None)
            ).all()
            
            confirmed = 0
            
            for payout in broadcast_payouts:
                try:
                    # Check transaction status via Mempool.space
                    url = f"{self.mempool_api}/tx/{payout.txid}"
                    
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(url)
                        
                        if response.status_code == 200:
                            tx_data = response.json()
                            status = tx_data.get('status', {})
                            
                            if status.get('confirmed'):
                                payout.status = 'confirmed'
                                payout.confirmed_at = datetime.utcnow()
                                confirmed += 1
                                
                                logger.info(f"[OK] Payout {payout.id} confirmed: {payout.txid}")
                
                except Exception as e:
                    logger.error(f"Error checking payout {payout.id}: {e}")
            
            if confirmed > 0:
                self.db.commit()
            
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
    
    def __init__(self, db: Session):
        self.db = db
        self.payout_engine = PayoutEngine(db)
    
    def process_detected_transaction(self, transaction: Transaction) -> Optional[Bet]:
        """
        Process a detected transaction into a bet
        
        Args:
            transaction: Detected transaction
            
        Returns:
            Bet object or None
        """
        try:
            # Check if bet already exists (must check this first!)
            existing_bet = self.db.query(Bet).filter(
                Bet.deposit_txid == transaction.txid
            ).first()
            
            if existing_bet:
                logger.info(f"Bet already exists for transaction {transaction.txid}")
                # Mark transaction as processed if not already
                if not transaction.is_processed:
                    transaction.is_processed = True
                    transaction.processed_at = datetime.utcnow()
                    self.db.commit()
                return existing_bet
            
            # Check if already processed but no bet found (shouldn't happen, but handle it)
            if transaction.is_processed:
                logger.warning(f"Transaction {transaction.txid} marked as processed but no bet found")
                return None
            
            # Get or create user
            from .database import User, DepositAddress, Seed
            
            user = self.db.query(User).filter(
                User.address == transaction.from_address
            ).first()
            
            if not user:
                user = User(
                    address=transaction.from_address,
                    total_bets=0,
                    total_wagered=0,
                    total_won=0,
                    total_lost=0
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            
            # Get deposit address info for bet parameters
            deposit_addr = self.db.query(DepositAddress).filter(
                DepositAddress.address == transaction.to_address
            ).first()
            
            # Determine multiplier (default or from deposit address)
            multiplier = deposit_addr.expected_multiplier if deposit_addr and deposit_addr.expected_multiplier else 2.0
            
            # Get or create active seed for user
            seed = self.db.query(Seed).filter(
                Seed.user_id == user.id,
                Seed.is_active == True
            ).first()
            
            if not seed:
                from .provably_fair import generate_new_seed_pair
                
                server_seed, server_seed_hash, client_seed = generate_new_seed_pair(user.address)
                
                seed = Seed(
                    user_id=user.id,
                    server_seed=server_seed,
                    server_seed_hash=server_seed_hash,
                    client_seed=client_seed,
                    nonce=0,
                    is_active=True
                )
                self.db.add(seed)
                self.db.commit()
                self.db.refresh(seed)
            
            # Validate bet parameters
            is_valid, error = ProvablyFair.validate_bet_params(transaction.amount, multiplier)
            
            if not is_valid:
                logger.error(f"Invalid bet parameters: {error}")
                transaction.is_processed = True
                transaction.processed_at = datetime.utcnow()
                self.db.commit()
                return None
            
            # Calculate win chance
            win_chance = ProvablyFair.calculate_win_chance(multiplier)
            
            # Create bet
            bet = Bet(
                user_id=user.id,
                seed_id=seed.id,
                bet_amount=transaction.amount,
                target_multiplier=multiplier,
                win_chance=win_chance,
                nonce=seed.nonce,
                deposit_txid=transaction.txid,
                deposit_address=transaction.to_address,
                status='pending'
            )
            
            self.db.add(bet)
            
            # Link transaction to bet
            transaction.bet_id = bet.id
            transaction.is_processed = True
            transaction.processed_at = datetime.utcnow()
            
            # Mark deposit address as used
            if deposit_addr:
                deposit_addr.is_used = True
                deposit_addr.used_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bet)
            
            logger.info(f"[OK] Created bet {bet.id} from transaction {transaction.txid}")
            
            # Check if should roll immediately (for 0-conf bets)
            if transaction.confirmations >= config.MIN_CONFIRMATIONS_PAYOUT:
                self.roll_and_payout_bet(bet)
            
            return bet
            
        except Exception as e:
            logger.error(f"Error processing transaction {transaction.txid}: {e}")
            self.db.rollback()
            return None
    
    def roll_and_payout_bet(self, bet: Bet) -> bool:
        """
        Roll dice and process payout for a bet
        
        Args:
            bet: Bet object
            
        Returns:
            True if successful
        """
        try:
            # Check if already rolled
            if bet.roll_result is not None:
                logger.info(f"Bet {bet.id} already rolled")
                return True
            
            # Get seed
            from .database import Seed
            seed = self.db.query(Seed).filter(Seed.id == bet.seed_id).first()
            
            if not seed:
                logger.error(f"Seed not found for bet {bet.id}")
                return False
            
            # Roll the dice
            from .provably_fair import ProvablyFair
            
            result = ProvablyFair.create_bet_result(
                server_seed=seed.server_seed,
                client_seed=seed.client_seed,
                nonce=bet.nonce,
                bet_amount=bet.bet_amount,
                multiplier=bet.target_multiplier
            )
            
            # Update bet with result
            bet.roll_result = result['roll']
            bet.is_win = result['is_win']
            bet.payout_amount = result['payout']
            bet.profit = result['profit']
            bet.rolled_at = datetime.utcnow()
            bet.status = 'rolled'
            
            # Increment seed nonce
            seed.nonce += 1
            
            # Update user statistics
            bet.user.total_bets += 1
            bet.user.total_wagered += bet.bet_amount
            
            if bet.is_win:
                bet.user.total_won += bet.profit
            else:
                bet.user.total_lost += abs(bet.profit)
            
            self.db.commit()
            
            logger.info(f"[DICE] Bet {bet.id} rolled: {result['roll']} ({'WIN' if result['is_win'] else 'LOSE'}) profit={result['profit']}")
            
            # Process payout if winner
            if bet.is_win and bet.payout_amount > 0:
                payout = self.payout_engine.process_winning_bet(bet)
                
                if payout:
                    bet.payout_txid = payout.txid
                    self.db.commit()
            else:
                # Mark as paid (house keeps it)
                bet.status = 'paid'
                bet.paid_at = datetime.utcnow()
                self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error rolling bet {bet.id}: {e}")
            self.db.rollback()
            return False
    
    def process_pending_bets(self) -> int:
        """
        Process all pending bets that have sufficient confirmations
        
        Returns:
            Number of bets processed
        """
        try:
            from .database import Bet
            
            # Get pending/confirmed bets
            pending_bets = self.db.query(Bet).filter(
                Bet.status.in_(['pending', 'confirmed']),
                Bet.roll_result.is_(None)
            ).all()
            
            processed = 0
            
            for bet in pending_bets:
                # Check confirmations
                if bet.transaction:
                    if bet.transaction.confirmations >= config.MIN_CONFIRMATIONS_PAYOUT:
                        bet.status = 'confirmed'
                        bet.confirmed_at = datetime.utcnow()
                        self.db.commit()
                        
                        # Roll and payout
                        if self.roll_and_payout_bet(bet):
                            processed += 1
            
            if processed > 0:
                logger.info(f"[OK] Processed {processed} bet(s)")
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing pending bets: {e}")
            return 0
