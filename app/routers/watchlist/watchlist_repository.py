from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from app.database import get_collection

class WatchlistRepository:
    """Repository for handling watchlist database operations"""
    
    COLLECTION_NAME = "watchlist"
    
    @staticmethod
    async def create_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new watchlist"""
        # Add timestamps
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = data["created_at"]
        
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.insert_one(data)
        
        # Get the created document
        if result.inserted_id:
            return await WatchlistRepository.get_watchlist_by_id(result.inserted_id)
        return None
    
    @staticmethod
    async def get_all_watchlists() -> List[Dict[str, Any]]:
        """Get all watchlists"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        cursor = collection.find()
        watchlists = await cursor.to_list(length=100)  # Limit to 100 items
        return watchlists
    
    @staticmethod
    async def get_watchlist_by_id(id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get a watchlist by its ID"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        return await collection.find_one({"_id": id})
    
    @staticmethod
    async def update_watchlist(id: ObjectId, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing watchlist"""
        # Add updated timestamp
        data["updated_at"] = datetime.utcnow()
        
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
    async def add_item_to_watchlist(id: ObjectId, item: str) -> Optional[Dict[str, Any]]:
        """Add an item to a watchlist's list field"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.update_one(
            {"_id": id},
            {
                "$addToSet": {"list": item},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count:
            return await WatchlistRepository.get_watchlist_by_id(id)
        return None
    
    @staticmethod
    async def remove_item_from_watchlist(id: ObjectId, item: str) -> Optional[Dict[str, Any]]:
        """Remove an item from a watchlist's list field"""
        collection = await get_collection(WatchlistRepository.COLLECTION_NAME)
        result = await collection.update_one(
            {"_id": id},
            {
                "$pull": {"list": item},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count:
            return await WatchlistRepository.get_watchlist_by_id(id)
        return None
