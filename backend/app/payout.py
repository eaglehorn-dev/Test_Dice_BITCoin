"""
Payout Engine
Automatic payout processing for winning bets
Handles Bitcoin transaction creation and broadcasting
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from blockcypher import simple_spend, create_unsigned_tx, make_tx_signatures, broadcast_signed_transaction
import requests

from .config import config
from .database import Bet, Payout, Transaction
from .provably_fair import ProvablyFair

logger = logging.getLogger(__name__)


class PayoutEngine:
    """Automated payout processing engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_token = config.BLOCKCYPHER_API_TOKEN
        self.house_private_key = config.HOUSE_PRIVATE_KEY
        self.house_address = config.HOUSE_ADDRESS
    
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
            success = self._broadcast_payout(payout)
            
            if success:
                bet.status = 'paid'
                bet.paid_at = datetime.utcnow()
                self.db.commit()
            
            return payout
            
        except Exception as e:
            logger.error(f"Error processing winning bet {bet.id}: {e}")
            self.db.rollback()
            return None
    
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
    
    def _broadcast_payout(self, payout: Payout) -> bool:
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
            
            # Use BlockCypher simple_spend API
            logger.info(f"Broadcasting payout {payout.id}: {payout.amount} sats to {payout.to_address}")
            
            result = self._send_bitcoin(
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
    
    def _send_bitcoin(self, to_address: str, amount_satoshis: int, from_private_key: str) -> Optional[dict]:
        """
        Send Bitcoin using BlockCypher API
        
        Args:
            to_address: Recipient address
            amount_satoshis: Amount to send in satoshis
            from_private_key: Sender's private key (WIF format)
            
        Returns:
            Transaction result dictionary or None
        """
        try:
            # Use BlockCypher simple_spend
            result = simple_spend(
                from_privkey=from_private_key,
                to_address=to_address,
                to_satoshis=amount_satoshis,
                coin_symbol='btc-testnet',
                api_key=self.api_token
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending Bitcoin: {e}")
            
            # Try alternative method using raw transaction
            try:
                return self._send_bitcoin_raw(to_address, amount_satoshis, from_private_key)
            except Exception as e2:
                logger.error(f"Alternative send method also failed: {e2}")
                return None
    
    def _send_bitcoin_raw(self, to_address: str, amount_satoshis: int, from_private_key: str) -> Optional[dict]:
        """
        Alternative method: Create and broadcast raw transaction
        
        Args:
            to_address: Recipient address
            amount_satoshis: Amount to send
            from_private_key: Private key in WIF format
            
        Returns:
            Transaction result or None
        """
        try:
            # This is a simplified version
            # In production, you'd want more sophisticated UTXO selection
            
            logger.info("Attempting raw transaction method")
            
            # For now, delegate back to simple_spend but with different params
            # In a real implementation, you'd use create_unsigned_tx, sign, and broadcast
            
            return None
            
        except Exception as e:
            logger.error(f"Error in raw transaction method: {e}")
            return None
    
    def retry_failed_payouts(self) -> int:
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
                
                success = self._broadcast_payout(payout)
                
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
    
    def check_payout_confirmations(self) -> int:
        """
        Check confirmations for broadcast payouts
        
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
                    # Check transaction status
                    from blockcypher import get_transaction_details
                    
                    tx_details = get_transaction_details(
                        payout.txid,
                        coin_symbol='btc-testnet',
                        api_key=self.api_token
                    )
                    
                    if tx_details:
                        confirmations = tx_details.get('confirmations', 0)
                        
                        if confirmations >= 1:
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
            # Check if already processed
            if transaction.is_processed:
                logger.info(f"Transaction {transaction.txid} already processed")
                return None
            
            # Check if bet already exists
            existing_bet = self.db.query(Bet).filter(
                Bet.deposit_txid == transaction.txid
            ).first()
            
            if existing_bet:
                logger.info(f"Bet already exists for transaction {transaction.txid}")
                transaction.is_processed = True
                transaction.processed_at = datetime.utcnow()
                self.db.commit()
                return existing_bet
            
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
