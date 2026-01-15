"""
Server Seed Service for Admin Backend
Manages server seeds (one per day)
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from bson import ObjectId
from loguru import logger

from app.utils.database import get_server_seeds_collection
from app.core.config import admin_config


class ServerSeedService:
    """Manages server seeds for provably fair system (one seed per day)"""
    
    def __init__(self):
        self.collection = get_server_seeds_collection()
    
    def _generate_server_seed(self) -> str:
        """Generate a cryptographically secure random server seed"""
        import secrets
        return secrets.token_hex(64)  # 128 character hex string
    
    def _hash_seed(self, seed: str) -> str:
        """Create SHA256 hash of server seed"""
        import hashlib
        return hashlib.sha256(seed.encode()).hexdigest()
    
    async def get_all_seeds(self) -> List[Dict[str, Any]]:
        """Get all server seeds (for admin)"""
        try:
            cursor = self.collection.find({}).sort("seed_date", -1)
            seeds = await cursor.to_list(length=None)
            return seeds
        except Exception as e:
            logger.error(f"Error getting all server seeds: {e}")
            return []
    
    async def create_server_seed(self, seed_date_str: str) -> Dict[str, Any]:
        """
        Create a server seed for a specific date (admin function)
        
        Args:
            seed_date_str: Date as ISO string (YYYY-MM-DD) - one seed per day
            
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
            
            # Generate new seed
            server_seed = self._generate_server_seed()
            server_seed_hash = self._hash_seed(server_seed)
            
            if existing:
                # Update existing seed
                seed_doc = {
                    "server_seed": server_seed,
                    "server_seed_hash": server_seed_hash,
                    "updated_at": datetime.utcnow()
                }
                
                await self.collection.update_one(
                    {"seed_date": seed_date_str},
                    {"$set": seed_doc}
                )
                
                # Get updated document
                updated = await self.collection.find_one({"seed_date": seed_date_str})
                logger.info(f"[ADMIN] Updated server seed for date {seed_date_str}: {server_seed_hash[:16]}...")
                return updated
            else:
                # Create new seed
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
        Only allows deletion of future dates (not past dates)
        
        Args:
            seed_id: Server seed ID to delete
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If trying to delete a past date's seed
        """
        try:
            from datetime import date
            
            # Get the seed to check its date
            seed = await self.collection.find_one({"_id": ObjectId(seed_id)})
            if not seed:
                return False
            
            seed_date_str = seed.get("seed_date")
            if seed_date_str:
                seed_date = datetime.strptime(seed_date_str, "%Y-%m-%d").date()
                today = date.today()
                
                if seed_date < today:
                    raise ValueError(f"Cannot delete server seed for past date {seed_date_str}")
            
            result = await self.collection.delete_one({"_id": ObjectId(seed_id)})
            return result.deleted_count > 0
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting server seed: {e}")
            return False
    
    async def get_seed_by_id(self, seed_id: str) -> Optional[Dict[str, Any]]:
        """Get server seed by ID"""
        try:
            seed = await self.collection.find_one({"_id": ObjectId(seed_id)})
            return seed
        except Exception as e:
            logger.error(f"Error getting server seed: {e}")
            return None
