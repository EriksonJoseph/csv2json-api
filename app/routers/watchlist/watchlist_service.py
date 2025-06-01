from typing import List, Dict, Any, Optional
from bson import ObjectId
from app.routers.watchlist.watchlist_repository import WatchlistRepository
from app.routers.watchlist.watchlist_model import WatchlistModel, WatchlistUpdate

class WatchlistService:
    """Service for handling watchlist business logic"""
    
    @staticmethod
    async def create_watchlist(watchlist_data: WatchlistModel) -> Dict[str, Any]:
        """Create a new watchlist"""
        # Convert Pydantic model to dict
        data = watchlist_data.dict(by_alias=True, exclude_unset=True)
        return await WatchlistRepository.create_watchlist(data)
    
    @staticmethod
    async def get_all_watchlists() -> List[Dict[str, Any]]:
        """Get all watchlists"""
        return await WatchlistRepository.get_all_watchlists()
    
    @staticmethod
    async def get_watchlist_by_id(id: str) -> Optional[Dict[str, Any]]:
        """Get a watchlist by ID"""
        try:
            object_id = ObjectId(id)
            return await WatchlistRepository.get_watchlist_by_id(object_id)
        except Exception:
            return None
    
    @staticmethod
    async def update_watchlist(id: str, update_data: WatchlistUpdate) -> Optional[Dict[str, Any]]:
        """Update an existing watchlist"""
        try:
            object_id = ObjectId(id)
            # Convert Pydantic model to dict, excluding unset fields
            data = update_data.dict(exclude_unset=True)
            return await WatchlistRepository.update_watchlist(object_id, data)
        except Exception:
            return None
    
    @staticmethod
    async def delete_watchlist(id: str) -> bool:
        """Delete a watchlist by ID"""
        try:
            object_id = ObjectId(id)
            return await WatchlistRepository.delete_watchlist(object_id)
        except Exception:
            return False
    
    @staticmethod
    async def add_item_to_watchlist(id: str, item: str) -> Optional[Dict[str, Any]]:
        """Add an item to a watchlist"""
        try:
            object_id = ObjectId(id)
            return await WatchlistRepository.add_item_to_watchlist(object_id, item)
        except Exception:
            return None
    
    @staticmethod
    async def remove_item_from_watchlist(id: str, item: str) -> Optional[Dict[str, Any]]:
        """Remove an item from a watchlist"""
        try:
            object_id = ObjectId(id)
            return await WatchlistRepository.remove_item_from_watchlist(object_id, item)
        except Exception:
            return None
