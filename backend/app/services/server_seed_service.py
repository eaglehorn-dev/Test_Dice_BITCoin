"""
Server Seed Service - Manages fixed server seeds (one per day)
"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from bson import ObjectId
from loguru import logger

from app.models.database import get_server_seeds_collection
from app.services.provably_fair_service import ProvablyFairService


class ServerSeedService:
    """Manages fixed server seeds for provably fair system (one seed per day)"""
    
    def __init__(self):
        self.collection = get_server_seeds_collection()
    
    async def get_today_server_seed(self) -> Optional[Dict[str, Any]]:
        """
        Get today's server seed (auto-generates and stores if doesn't exist)
        
        Returns:
            Today's server seed document (always returns a seed, never None)
        """
        try:
            today = date.today().isoformat()  # YYYY-MM-DD
            
            # Check if today's seed exists
            seed = await self.collection.find_one({"seed_date": today})
            
            if not seed:
                # Generate new server seed for today and store it
                server_seed = ProvablyFairService.generate_server_seed()
                server_seed_hash = ProvablyFairService.hash_seed(server_seed)
                
                seed_doc = {
                    "server_seed": server_seed,
                    "server_seed_hash": server_seed_hash,
                    "seed_date": today,
                    "created_at": datetime.utcnow(),
                    "bet_count": 0
                }
                
                result = await self.collection.insert_one(seed_doc)
                seed_doc["_id"] = result.inserted_id
                seed = seed_doc
                
                logger.info(f"Auto-generated and stored new server seed for today ({today}): {server_seed_hash[:16]}...")
            
            return seed
            
        except Exception as e:
            logger.error(f"Error getting today's server seed: {e}")
            return None
    
    async def ensure_today_server_seed(self) -> Dict[str, Any]:
        """
        Ensure there's a server seed for today, create one if needed
        (Alias for get_today_server_seed for backward compatibility)
        
        Returns:
            Today's server seed document
        """
        seed = await self.get_today_server_seed()
        if not seed:
            raise RuntimeError("Failed to get or create today's server seed")
        return seed
    
    async def increment_bet_count(self, seed_id: ObjectId):
        """Increment bet count for a server seed"""
        try:
            await self.collection.update_one(
                {"_id": seed_id},
                {"$inc": {"bet_count": 1}}
            )
        except Exception as e:
            logger.error(f"Error incrementing bet count: {e}")
    
    async def get_all_seeds(self) -> list:
        """Get all server seeds (for admin)"""
        try:
            cursor = self.collection.find({}).sort("seed_date", -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting all server seeds: {e}")
            return []
    
    async def create_server_seed_for_date(self, seed_date_str: str) -> Dict[str, Any]:
        """
        Create a server seed for a specific date (admin function)
        
        Args:
            seed_date_str: Date in YYYY-MM-DD format
            
        Returns:
            New server seed document
        """
        try:
            # Validate date format
            try:
                seed_date = datetime.strptime(seed_date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format: {seed_date_str}. Expected YYYY-MM-DD")
            
            # Check if seed already exists for this date
            existing = await self.collection.find_one({"seed_date": seed_date_str})
            if existing:
                raise ValueError(f"Server seed already exists for date {seed_date_str}")
            
            # Generate new seed
            server_seed = ProvablyFairService.generate_server_seed()
            server_seed_hash = ProvablyFairService.hash_seed(server_seed)
            
            seed_doc = {
                "server_seed": server_seed,
                "server_seed_hash": server_seed_hash,
                "seed_date": seed_date_str,
                "created_at": datetime.utcnow(),
                "bet_count": 0
            }
            
            result = await self.collection.insert_one(seed_doc)
            seed_doc["_id"] = result.inserted_id
            
            logger.info(f"[ADMIN] Created server seed for date {seed_date_str}: {server_seed_hash[:16]}...")
            
            return seed_doc
            
        except Exception as e:
            logger.error(f"Error creating server seed: {e}")
            raise
    
    async def delete_seed(self, seed_id: str) -> bool:
        """
        Delete a server seed (admin function)
        
        Args:
            seed_id: Server seed ID to delete
            
        Returns:
            True if successful
        """
        try:
            from bson import ObjectId
            result = await self.collection.delete_one({"_id": ObjectId(seed_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting server seed: {e}")
            return False
