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
from app.utils.counter import get_next_bet_number
from .provably_fair_service import ProvablyFairService, generate_new_seed_pair
from .payout_service import PayoutService
from .wallet_service import WalletService


class BetService:
    """Service for bet business logic"""
    
    def __init__(self):
        self.bet_repo = BetRepository()
        self.user_repo = UserRepository()
        self.tx_repo = TransactionRepository()
        self.payout_service = PayoutService()
        self.fair_service = ProvablyFairService()
        self.wallet_service = WalletService()
    
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
            
            user = await self.user_repo.get_or_create(transaction_dict["from_address"])
            
            target_address = transaction_dict["to_address"]
            
            wallet = await self.wallet_service.get_wallet_by_address(target_address)
            if not wallet:
                logger.error(f"Wallet not found for address {target_address[:10]}... - cannot create bet")
                return None
            
            multiplier_int = wallet["multiplier"]
            multiplier_float = float(multiplier_int)
            
            logger.info(f"[BET] Using {multiplier_int}x wallet for bet")
            
            # Get or create user seed (for client_seed and nonce tracking)
            seeds_col = get_seeds_collection()
            user_seed = await seeds_col.find_one({"user_id": user["_id"], "is_active": True})
            
            if not user_seed:
                # Create user seed record (client_seed = user address, nonce starts at 0)
                client_seed = user["address"]
                
                user_seed_doc = {
                    "user_id": user["_id"],
                    "client_seed": client_seed,
                    "nonce": 0,
                    "is_active": True,
                    "revealed_at": None,
                    "created_at": datetime.utcnow()
                }
                result = await seeds_col.insert_one(user_seed_doc)
                user_seed_doc["_id"] = result.inserted_id
                user_seed = user_seed_doc
            
            # Get today's server seed (one seed per day)
            from app.services.server_seed_service import ServerSeedService
            server_seed_service = ServerSeedService()
            server_seed_doc = await server_seed_service.ensure_today_server_seed()
            
            # Increment server seed bet count
            await server_seed_service.increment_bet_count(server_seed_doc["_id"])
            
            # Combine server seed and user seed for bet processing
            seed = {
                "_id": user_seed["_id"],
                "server_seed": server_seed_doc["server_seed"],
                "server_seed_hash": server_seed_doc["server_seed_hash"],
                "client_seed": user_seed["client_seed"],
                "nonce": user_seed["nonce"],
                "user_id": user_seed["user_id"]
            }
            
            # Broadcast seed hash update if this is a new server seed (first bet of the day)
            if server_seed_doc.get("bet_count", 0) == 1:  # First bet with today's seed
                try:
                    from app.utils.websocket_manager import manager
                    await manager.broadcast({
                        "type": "seed_hash_update",
                        "server_seed_hash": server_seed_doc["server_seed_hash"],
                        "seed_date": server_seed_doc.get("seed_date")
                    })
                    logger.info(f"📡 [WEBSOCKET] Broadcast new server seed hash for {server_seed_doc.get('seed_date', 'today')}: {server_seed_doc['server_seed_hash'][:16]}...")
                except Exception as e:
                    logger.warning(f"Failed to broadcast seed hash update: {e}")
            
            is_valid, error = self.fair_service.validate_bet_params(transaction_dict["amount"], multiplier_float)
            
            if not is_valid:
                logger.error(f"Invalid bet parameters: {error}")
                await self.tx_repo.mark_processed(transaction_dict["txid"])
                return None
            
            # Get chance from wallet (use default if not set for backward compatibility)
            chance = wallet.get("chance")
            if chance is None:
                # Calculate default chance for old wallets without chance field
                chance = self.fair_service.calculate_win_chance(multiplier_float)
                logger.warning(f"Wallet {wallet['_id']} missing chance field, using calculated: {chance}%")
            
            # Get next incremental bet number
            bet_number = await get_next_bet_number()
            
            bet_doc = {
                "bet_number": bet_number,  # Incremental bet ID (1, 2, 3, ...)
                "user_id": user["_id"],
                "seed_id": seed["_id"],
                "server_seed": seed["server_seed"],  # Save server seed in bet for history
                "server_seed_hash": seed["server_seed_hash"],  # Save hash for verification
                "client_seed": seed["client_seed"],  # Save client seed for verification
                "bet_amount": transaction_dict["amount"],
                "target_multiplier": multiplier_float,
                "multiplier": multiplier_int,
                "target_address": target_address,
                "wallet_id": wallet["_id"],
                "win_chance": chance,  # Use wallet's chance value
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
            
            await self.tx_repo.mark_processed(transaction_dict["txid"], bet_id)
            
            await self.wallet_service.record_transaction(
                wallet_id=str(wallet["_id"]),
                received=transaction_dict["amount"]
            )
            
            logger.info(f"[OK] Created {multiplier_int}x bet #{bet_number} (ID: {bet_doc['_id']}) from transaction {transaction_dict['txid']}")
            
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
            
            # Get user seed (for client_seed and nonce)
            seeds_col = get_seeds_collection()
            user_seed = await seeds_col.find_one({"_id": bet_dict["seed_id"]})
            
            if not user_seed:
                logger.error(f"User seed not found for bet {bet_dict['_id']}")
                return False
            
            # Get server seed (fixed, shared across all users)
            # For old bets, server_seed might be stored in bet_dict
            server_seed = bet_dict.get("server_seed")
            if not server_seed:
                # Try to get from active server seed
                from app.services.server_seed_service import ServerSeedService
                server_seed_service = ServerSeedService()
                server_seed_doc = await server_seed_service.get_active_server_seed()
                if server_seed_doc:
                    server_seed = server_seed_doc["server_seed"]
                else:
                    logger.error(f"Server seed not found for bet {bet_dict['_id']}")
                    return False
            
            # Get chance from bet (stored when bet was created)
            bet_chance = bet_dict.get("win_chance")
            if bet_chance is None:
                # Fallback: calculate from multiplier (for old bets)
                bet_chance = self.fair_service.calculate_win_chance(bet_dict["target_multiplier"])
                logger.warning(f"Bet {bet_dict['_id']} missing win_chance, using calculated: {bet_chance}%")
            
            # Roll the dice
            result = self.fair_service.create_bet_result(
                server_seed=server_seed,
                client_seed=user_seed["client_seed"],
                nonce=bet_dict["nonce"],
                bet_amount=bet_dict["bet_amount"],
                multiplier=bet_dict["target_multiplier"],
                chance=bet_chance
            )
            
            # Update bet with result
            await self.bet_repo.update_result(
                bet_dict["_id"],
                result["roll"],
                result["is_win"],
                result["payout"],
                result["profit"]
            )
            
            # Increment user seed nonce (for next bet)
            await seeds_col.update_one(
                {"_id": bet_dict["seed_id"]},
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
            payout_txid = None
            if result["is_win"] and result["payout"] > 0:
                payout = await self.payout_service.process_winning_bet(bet_dict)
                
                if payout and payout.get("txid"):
                    payout_txid = payout["txid"]
                    await self.bet_repo.update_by_id(
                        bet_dict["_id"],
                        {"$set": {"payout_txid": payout_txid}}
                    )
            else:
                # Mark as paid (house keeps it) - payout_txid remains None for losses
                await self.bet_repo.update_status(bet_dict["_id"], "paid")
            
            # Fetch updated bet with payout_txid before broadcasting
            updated_bet = await self.bet_repo.find_by_id(bet_dict["_id"])
            if updated_bet:
                bet_dict = updated_bet
            
            # Broadcast bet result AFTER storing everything
            try:
                from app.utils.mempool_websocket import MempoolWebSocket
                # Get the singleton instance if available
                # Note: This assumes mempool_websocket is already initialized
                # We'll broadcast via the websocket manager instead
                from app.utils.websocket_manager import manager
                from app.models.database import get_users_collection
                from bson import ObjectId
                
                users_col = get_users_collection()
                user = await users_col.find_one({"_id": ObjectId(bet_dict["user_id"])})
                
                bet_data = {
                    "bet_id": str(bet_dict["_id"]),
                    "bet_number": bet_dict.get("bet_number"),
                    "user_address": user["address"] if user else None,
                    "bet_amount": bet_dict["bet_amount"],
                    "target_multiplier": bet_dict["target_multiplier"],
                    "multiplier": bet_dict.get("multiplier", int(bet_dict["target_multiplier"])),
                    "win_chance": bet_dict["win_chance"],
                    "roll_result": bet_dict.get("roll_result"),
                    "is_win": bet_dict.get("is_win"),
                    "payout_amount": bet_dict.get("payout_amount"),
                    "profit": bet_dict.get("profit"),
                    "nonce": bet_dict.get("nonce"),
                    "target_address": bet_dict.get("target_address"),
                    "deposit_txid": bet_dict.get("deposit_txid"),
                    "payout_txid": bet_dict.get("payout_txid"),  # Include payout_txid (None for losses)
                    "server_seed": bet_dict.get("server_seed"),
                    "server_seed_hash": bet_dict.get("server_seed_hash"),
                    "client_seed": bet_dict.get("client_seed"),
                    "status": bet_dict["status"],
                    "created_at": bet_dict["created_at"].isoformat() if bet_dict.get("created_at") else None,
                    "rolled_at": bet_dict.get("rolled_at").isoformat() if bet_dict.get("rolled_at") else None
                }
                
                await manager.broadcast({
                    "type": "new_bet",
                    "bet": bet_data
                })
                
                logger.info(f"📡 [WEBSOCKET] Broadcast bet {bet_dict['_id']} result after storing payout_txid")
            except Exception as e:
                logger.error(f"Error broadcasting bet result: {e}")
            
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
