from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId
from app.routers.watchlist.watchlist_repository import WatchlistRepository
from app.routers.watchlist.watchlist_model import WatchlistModel, WatchlistUpdate

class WatchlistService:
    """Service for handling watchlist business logic"""
    
    @staticmethod
    async def create_watchlist(watchlist_data: WatchlistModel, user_id: str) -> Optional[Dict[str, Any]]:
        """Create a new watchlist"""
        # Convert Pydantic model to dict
        data: Dict[str, Any] = watchlist_data.dict(by_alias=True, exclude_unset=True)
        result = await WatchlistRepository.create_watchlist(data, user_id)
        return result
    
    @staticmethod
    async def get_all_watchlists(page: int = 1, limit: int = 10, user_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Get all watchlists with pagination"""
        return await WatchlistRepository.get_all_watchlists(page, limit)
    
    @staticmethod
    async def get_watchlist_by_id(id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a watchlist by ID"""
        try:
            object_id: ObjectId = ObjectId(id)
            return await WatchlistRepository.get_watchlist_by_id(object_id)
        except Exception:
            return None
    
    @staticmethod
    async def update_watchlist(id: str, update_data: WatchlistUpdate, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update an existing watchlist"""
        try:
            object_id: ObjectId = ObjectId(id)
            # Convert Pydantic model to dict, excluding unset fields
            data: Dict[str, Any] = update_data.dict(exclude_unset=True)
            if user_id is None:
                raise ValueError("user_id is required for updating watchlist")
            return await WatchlistRepository.update_watchlist(object_id, data, user_id)
        except Exception:
            return None
    
    @staticmethod
    async def delete_watchlist(id: str, user_id: Optional[str] = None) -> bool:
        """Delete a watchlist by ID"""
        try:
            object_id: ObjectId = ObjectId(id)
            return await WatchlistRepository.delete_watchlist(object_id)
        except Exception:
            return False
    
    @staticmethod
    async def add_item_to_watchlist(id: str, item: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Add an item to a watchlist"""
        try:
            object_id: ObjectId = ObjectId(id)
            if user_id is None:
                raise ValueError("user_id is required for adding item to watchlist")
            return await WatchlistRepository.add_item_to_watchlist(object_id, item, user_id)
        except Exception:
            return None
    
    @staticmethod
    async def remove_item_from_watchlist(id: str, item: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Remove an item from a watchlist"""
        try:
            object_id: ObjectId = ObjectId(id)
            if user_id is None:
                raise ValueError("user_id is required for removing item from watchlist")
            return await WatchlistRepository.remove_item_from_watchlist(object_id, item, user_id)
        except Exception:
            return None
