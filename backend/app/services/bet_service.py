"""
Bet Service - Business logic for bet processing
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from loguru import logger

from app.core.config import config
from app.core.exceptions import InvalidBetException, BetNotFoundException
from app.repository.bet_repository import BetRepository
from app.repository.user_repository import UserRepository
from app.repository.transaction_repository import TransactionRepository
from app.repository.payout_repository import PayoutRepository
from app.models.database import get_seeds_collection, get_deposit_addresses_collection
from .provably_fair_service import ProvablyFairService, generate_new_seed_pair
from .payout_service import PayoutService


class BetService:
    """Service for bet business logic"""
    
    def __init__(self):
        self.bet_repo = BetRepository()
        self.user_repo = UserRepository()
        self.tx_repo = TransactionRepository()
        self.payout_service = PayoutService()
        self.fair_service = ProvablyFairService()
    
    async def process_detected_transaction(self, transaction_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a detected transaction into a bet
        
        Args:
            transaction_dict: Detected transaction dictionary
            
        Returns:
            Bet dictionary or None
        """
        try:
            # Check if bet already exists
            existing_bet = await self.bet_repo.get_by_deposit_txid(transaction_dict["txid"])
            
            if existing_bet:
                logger.info(f"Bet already exists for transaction {transaction_dict['txid']}")
                # Mark transaction as processed if not already
                if not transaction_dict.get("is_processed"):
                    await self.tx_repo.mark_processed(transaction_dict["txid"], existing_bet["_id"])
                return existing_bet
            
            # Check if already processed
            if transaction_dict.get("is_processed"):
                logger.warning(f"Transaction {transaction_dict['txid']} marked as processed but no bet found")
                return None
            
            # Get or create user
            user = await self.user_repo.get_or_create(transaction_dict["from_address"])
            
            # Get deposit address info for bet parameters
            deposit_addrs_col = get_deposit_addresses_collection()
            deposit_addr = await deposit_addrs_col.find_one({"address": transaction_dict["to_address"]})
            
            # Determine multiplier
            multiplier = deposit_addr.get("expected_multiplier", 2.0) if deposit_addr else 2.0
            
            # Get or create active seed for user
            seeds_col = get_seeds_collection()
            seed = await seeds_col.find_one({"user_id": user["_id"], "is_active": True})
            
            if not seed:
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
            is_valid, error = self.fair_service.validate_bet_params(transaction_dict["amount"], multiplier)
            
            if not is_valid:
                logger.error(f"Invalid bet parameters: {error}")
                await self.tx_repo.mark_processed(transaction_dict["txid"])
                return None
            
            # Calculate win chance
            win_chance = self.fair_service.calculate_win_chance(multiplier)
            
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
            
            bet_id = await self.bet_repo.insert_one(bet_doc)
            bet_doc["_id"] = bet_id
            
            # Link transaction to bet
            await self.tx_repo.mark_processed(transaction_dict["txid"], bet_id)
            
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
            # Check if already rolled
            if bet_dict.get("roll_result") is not None:
                logger.info(f"Bet {bet_dict['_id']} already rolled")
                return True
            
            # Get seed
            seeds_col = get_seeds_collection()
            seed = await seeds_col.find_one({"_id": bet_dict["seed_id"]})
            
            if not seed:
                logger.error(f"Seed not found for bet {bet_dict['_id']}")
                return False
            
            # Roll the dice
            result = self.fair_service.create_bet_result(
                server_seed=seed["server_seed"],
                client_seed=seed["client_seed"],
                nonce=bet_dict["nonce"],
                bet_amount=bet_dict["bet_amount"],
                multiplier=bet_dict["target_multiplier"]
            )
            
            # Update bet with result
            await self.bet_repo.update_result(
                bet_dict["_id"],
                result["roll"],
                result["is_win"],
                result["payout"],
                result["profit"]
            )
            
            # Increment seed nonce
            await seeds_col.update_one(
                {"_id": seed["_id"]},
                {"$inc": {"nonce": 1}}
            )
            
            # Update user statistics
            await self.user_repo.update_stats(
                (await self.user_repo.find_by_id(bet_dict["user_id"]))["address"],
                bet_dict["bet_amount"],
                result["profit"],
                result["is_win"]
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
                payout = await self.payout_service.process_winning_bet(bet_dict)
                
                if payout and payout.get("txid"):
                    await self.bet_repo.update_by_id(
                        bet_dict["_id"],
                        {"$set": {"payout_txid": payout["txid"]}}
                    )
            else:
                # Mark as paid (house keeps it)
                await self.bet_repo.update_status(bet_dict["_id"], "paid")
            
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
            # Get pending bets
            pending_bets = await self.bet_repo.get_pending_bets()
            
            processed = 0
            
            for bet in pending_bets:
                # Check confirmations
                if bet.get("deposit_txid"):
                    tx = await self.tx_repo.get_by_txid(bet["deposit_txid"])
                    if tx and tx.get("confirmations", 0) >= config.MIN_CONFIRMATIONS_PAYOUT:
                        await self.bet_repo.update_status(bet["_id"], "confirmed", confirmed_at=datetime.utcnow())
                        
                        # Roll and payout
                        if await self.roll_and_payout_bet(bet):
                            processed += 1
            
            if processed > 0:
                logger.info(f"[OK] Processed {processed} bet(s)")
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing pending bets: {e}")
            return 0
    
    async def get_bet_by_id(self, bet_id: str) -> Dict[str, Any]:
        """Get bet by ID"""
        bet = await self.bet_repo.find_by_id(ObjectId(bet_id))
        if not bet:
            raise BetNotFoundException(f"Bet {bet_id} not found")
        return bet
    
    async def get_user_bets(self, user_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get bets for a user"""
        user = await self.user_repo.get_by_address(user_address)
        if not user:
            return []
        
        return await self.bet_repo.get_by_user(user["_id"], limit=limit)
    
    async def get_recent_bets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent bets from all users"""
        return await self.bet_repo.get_recent_bets(limit=limit)
