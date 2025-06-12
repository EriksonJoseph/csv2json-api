from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import List, Dict, Any, Optional
from app.routers.watchlist.watchlist_model import WatchlistModel, WatchlistResponse, WatchlistUpdate
from app.routers.watchlist.watchlist_service import WatchlistService
from app.utils.serializers import individual_serial
from app.dependencies.auth import get_current_user
from app.api.schemas import PaginationResponse

# Create router
router = APIRouter(
    prefix="/watchlist",
    tags=["watchlist"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/", 
    response_model=WatchlistResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new watchlist"
)
async def create_watchlist(
    watchlist: WatchlistModel = Body(...),
    current_user: Any = Depends(get_current_user)
) -> WatchlistResponse:
    """
    Create a new watchlist with the following information:
    
    - **title**: Title of the watchlist
    - **list**: List of items to watch (optional)
    """
    result = await WatchlistService.create_watchlist(watchlist, current_user.user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to create watchlist"
        )
    return WatchlistResponse(**individual_serial(result))

@router.get(
    "/", 
    response_model=PaginationResponse[WatchlistResponse],
    summary="Get all watchlists"
)
async def get_all_watchlists(
    page: int = 1,
    limit: int = 10,
    current_user: Any = Depends(get_current_user)
) -> PaginationResponse[WatchlistResponse]:
    """
    Retrieve all watchlists with pagination
    """
    watchlists, total = await WatchlistService.get_all_watchlists(page, limit, current_user.user_id)
    
    # Format watchlists for response (remove timestamps and keep only necessary fields)
    formatted_watchlists: List[Dict[str, Any]] = []
    for watchlist in watchlists:
        formatted_watchlist: Dict[str, Any] = {
            "_id": str(watchlist["_id"]),
            "title": watchlist["title"],
            "list": watchlist["list"]
        }
        formatted_watchlists.append(formatted_watchlist)
    
    return PaginationResponse(
        list=formatted_watchlists,
        total=total,
        page=page,
        limit=limit
    )

@router.get(
    "/{id}", 
    response_model=WatchlistResponse,
    summary="Get a specific watchlist by ID"
)
async def get_watchlist(
    id: str,
    current_user: Any = Depends(get_current_user)
) -> WatchlistResponse:
    """
    Retrieve a specific watchlist by its ID
    """
    watchlist = await WatchlistService.get_watchlist_by_id(id, current_user.user_id)
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Watchlist with ID {id} not found"
        )
    return WatchlistResponse(**individual_serial(watchlist))

@router.put(
    "/{id}", 
    response_model=WatchlistResponse,
    summary="Update a watchlist"
)
async def update_watchlist(
    id: str,
    watchlist_update: WatchlistUpdate = Body(...),
    current_user: Any = Depends(get_current_user)
) -> WatchlistResponse:
    """
    Update a watchlist with the following information:
    
    - **title**: New title for the watchlist (optional)
    - **list**: New list of items to watch (optional)
    """
    # First check if watchlist exists
    existing = await WatchlistService.get_watchlist_by_id(id, current_user.user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Watchlist with ID {id} not found"
        )
    
    updated = await WatchlistService.update_watchlist(id, watchlist_update, current_user.user_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to update watchlist"
        )
    return WatchlistResponse(**individual_serial(updated))

@router.delete(
    "/{id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a watchlist"
)
async def delete_watchlist(
    id: str,
    current_user: Any = Depends(get_current_user)
) -> None:
    """
    Delete a watchlist by its ID
    """
    # First check if watchlist exists
    existing = await WatchlistService.get_watchlist_by_id(id, current_user.user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Watchlist with ID {id} not found"
        )
    
    deleted = await WatchlistService.delete_watchlist(id, current_user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to delete watchlist"
        )
    return None

@router.post(
    "/{id}/items", 
    response_model=WatchlistResponse,
    summary="Add an item to a watchlist"
)
async def add_item_to_watchlist(
    id: str,
    item: str = Body(..., embed=True),
    current_user: Any = Depends(get_current_user)
) -> WatchlistResponse:
    """
    Add a single item to a watchlist's list
    
    - **item**: Item to add to the watchlist
    """
    # First check if watchlist exists
    existing = await WatchlistService.get_watchlist_by_id(id, current_user.user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Watchlist with ID {id} not found"
        )
    
    updated = await WatchlistService.add_item_to_watchlist(id, item, current_user.user_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to add item to watchlist"
        )
    return WatchlistResponse(**individual_serial(updated))

@router.delete(
    "/{id}/items/{item}", 
    response_model=WatchlistResponse,
    summary="Remove an item from a watchlist"
)
async def remove_item_from_watchlist(
    id: str,
    item: str,
    current_user: Any = Depends(get_current_user)
) -> WatchlistResponse:
    """
    Remove a single item from a watchlist's list
    """
    # First check if watchlist exists
    existing = await WatchlistService.get_watchlist_by_id(id, current_user.user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Watchlist with ID {id} not found"
        )
    
    updated = await WatchlistService.remove_item_from_watchlist(id, item, current_user.user_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to remove item from watchlist"
        )
    return WatchlistResponse(**individual_serial(updated))
