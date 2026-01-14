"""
Base Repository with common CRUD operations
"""
from typing import Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from loguru import logger

from app.core.exceptions import DatabaseException


class BaseRepository:
    """Base repository with common database operations"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def find_by_id(self, doc_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Find document by ID"""
        try:
            return await self.collection.find_one({"_id": doc_id})
        except Exception as e:
            logger.error(f"Error finding document by ID: {e}")
            raise DatabaseException(f"Failed to find document: {str(e)}")
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single document by query"""
        try:
            return await self.collection.find_one(query)
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            raise DatabaseException(f"Failed to find document: {str(e)}")
    
    async def find_many(
        self,
        query: Dict[str, Any],
        limit: int = 100,
        skip: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)
            if sort:
                cursor = cursor.sort(sort)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error finding documents: {e}")
            raise DatabaseException(f"Failed to find documents: {str(e)}")
    
    async def insert_one(self, document: Dict[str, Any]) -> ObjectId:
        """Insert single document"""
        try:
            result = await self.collection.insert_one(document)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            raise DatabaseException(f"Failed to insert document: {str(e)}")
    
    async def update_one(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> bool:
        """Update single document"""
        try:
            result = await self.collection.update_one(query, update)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise DatabaseException(f"Failed to update document: {str(e)}")
    
    async def update_by_id(
        self,
        doc_id: ObjectId,
        update: Dict[str, Any]
    ) -> bool:
        """Update document by ID"""
        return await self.update_one({"_id": doc_id}, update)
    
    async def delete_one(self, query: Dict[str, Any]) -> bool:
        """Delete single document"""
        try:
            result = await self.collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise DatabaseException(f"Failed to delete document: {str(e)}")
    
    async def delete_by_id(self, doc_id: ObjectId) -> bool:
        """Delete document by ID"""
        return await self.delete_one({"_id": doc_id})
    
    async def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query"""
        try:
            if query is None:
                query = {}
            return await self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            raise DatabaseException(f"Failed to count documents: {str(e)}")
    
    async def exists(self, query: Dict[str, Any]) -> bool:
        """Check if document exists"""
        count = await self.count(query)
        return count > 0
