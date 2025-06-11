from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database import get_collection

class WatchlistRepository:
    """Repository for handling watchlist database operations"""
    
    COLLECTION_NAME = "watchlist"
    
    @staticmethod
    async def create_watchlist(data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Create a new watchlist"""
        # Add timestamps and audit fields
        now = datetime.utcnow()
        data["created_at"] = now
        data["updated_at"] = now
        data["created_by"] = created_by
        data["updated_by"] = created_by
        
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.insert_one(data)
        
        # Get the created document
        if result.inserted_id:
            return await WatchlistRepository.get_watchlist_by_id(result.inserted_id)
        return None
    
    @staticmethod
    async def get_all_watchlists(page: int = 1, limit: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """Get all watchlists with pagination"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Count total watchlists
        total = await collection.count_documents({})
        
        # Get watchlists with pagination
        cursor = collection.find().sort("created_at", -1).skip(skip).limit(limit)
        watchlists = await cursor.to_list(length=limit)
        
        return watchlists, total
    
    @staticmethod
    async def get_watchlist_by_id(id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get a watchlist by its ID"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        return await collection.find_one({"_id": id})
    
    @staticmethod
    async def update_watchlist(id: ObjectId, data: Dict[str, Any], updated_by: str) -> Optional[Dict[str, Any]]:
        """Update an existing watchlist"""
        # Add updated timestamp and audit field
        data["updated_at"] = datetime.utcnow()
        data["updated_by"] = updated_by
        
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.update_one(
            {"_id": id},
            {"$set": data}
        )
        
        if result.modified_count:
            return await WatchlistRepository.get_watchlist_by_id(id)
        return None
    
    @staticmethod
    async def delete_watchlist(id: ObjectId) -> bool:
        """Delete a watchlist by ID"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.delete_one({"_id": id})
        return result.deleted_count > 0
    
    @staticmethod
    async def add_item_to_watchlist(id: ObjectId, item: str, updated_by: str) -> Optional[Dict[str, Any]]:
        """Add an item to a watchlist's list field"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.update_one(
            {"_id": id},
            {
                "$addToSet": {"list": item},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "updated_by": updated_by
                }
            }
        )
        
        if result.modified_count:
            return await WatchlistRepository.get_watchlist_by_id(id)
        return None
    
    @staticmethod
    async def remove_item_from_watchlist(id: ObjectId, item: str, updated_by: str) -> Optional[Dict[str, Any]]:
        """Remove an item from a watchlist's list field"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.update_one(
            {"_id": id},
            {
                "$pull": {"list": item},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "updated_by": updated_by
                }
            }
        )
        
        if result.modified_count:
            return await WatchlistRepository.get_watchlist_by_id(id)
        return None
