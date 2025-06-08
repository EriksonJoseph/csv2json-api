from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, Any
from app.api.schemas.pagination import PaginationResponse
from app.routers.matching.matching_service import MatchingService
from app.routers.matching.matching_model import (
    SingleSearchRequest, BulkSearchRequest, SingleSearchResponse, 
    BulkSearchResponse, AvailableColumnsResponse, SearchHistoryResponse
)
from app.dependencies.auth import get_current_user, require_user
from app.utils.advanced_performance import tracker
from app.exceptions import TaskException

router = APIRouter(
    prefix="/matching",
    tags=["matching"],
    responses={404: {"description": "Not Found"}}
)

# Initialize service
matching_service = MatchingService()

@router.get("/columns/{task_id}", response_model=AvailableColumnsResponse)
@tracker.measure_async_time
async def get_available_columns(
    task_id: str = Path(..., description="Task ID to get columns for"),
    current_user = Depends(require_user)
):
    """
    📋 Get available columns for fuzzy matching
    
    This endpoint returns all available columns in the CSV data for a specific task,
    along with recommended columns for name matching.
    """
    try:
        return await matching_service.get_available_columns(task_id)
    except TaskException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/search", response_model=SingleSearchResponse)
@tracker.measure_async_time
async def single_search(
    request: SingleSearchRequest,
    current_user = Depends(require_user)
):
    """
    🔍 Search for a single name using fuzzy matching
    
    This endpoint performs fuzzy matching for a single name against the specified
    columns in the CSV data. Returns all matches above the threshold with confidence scores.
    
    **Example Request:**
    ```json
    {
        "task_id": "65f1b2c3d4e5f6789abcdef0",
        "name": "John Smith",
        "threshold": 70,
        "columns": ["NameAlias_WholeName", "NameAlias_FirstName"]
    }
    ```
    """
    try:
        return await matching_service.single_search(request, current_user.user_id)
    except TaskException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/bulk-search", response_model=BulkSearchResponse)
@tracker.measure_async_time
async def bulk_search(
    request: BulkSearchRequest,
    current_user = Depends(require_user)
):
    """
    🔍 Search for multiple names using fuzzy matching
    
    This endpoint performs fuzzy matching for multiple names against the specified
    columns in the CSV data. Returns the best match for each name with confidence scores.
    
    **Example Request:**
    ```json
    {
        "task_id": "65f1b2c3d4e5f6789abcdef0",
        "threshold": 70,
        "columns": ["NameAlias_WholeName", "NameAlias_FirstName"],
        "list": ["John Smith", "Maria Garcia", "Ahmed Hassan"]
    }
    ```
    
    **Performance Note:** 
    For large lists (>1000 names), consider breaking them into smaller batches.
    """
    try:
        if len(request.list) > 1000:
            raise HTTPException(
                status_code=400, 
                detail="Maximum 1000 names per request. Please split into smaller batches."
            )
        
        return await matching_service.bulk_search(request, current_user.user_id)
    except TaskException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/result/{search_id}")
@tracker.measure_async_time
async def get_matching_result(
    search_id: str = Path(..., description="Search ID to get matching result for"),
    current_user = Depends(require_user)
):
    """
    📊 Get matching result for a specific search history
    
    Returns the detailed search result from search_history collection
    including all search parameters, execution details, and summary statistics.
    """
    try:
        return await matching_service.get_search_result(search_id)
    except TaskException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.get("/history", response_model=PaginationResponse[Dict[str, Any]])
@tracker.measure_async_time
async def get_search_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user = Depends(require_user)
):
    """
    📜 Get search history for the current user
    
    Returns a paginated list of previous searches performed by the current user.
    """
    try:
        history_data = await matching_service.get_search_history(
            current_user.user_id, page, limit
        )
        return history_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
@tracker.measure_async_time
async def health_check(current_user = Depends(require_user)):
    """
    🏥 Health check for matching service
    """
    return {
        "status": "healthy",
        "service": "matching",
        "message": "Fuzzy matching service is operational"
    }

@router.get("/stats/{task_id}")
@tracker.measure_async_time
async def get_task_stats(
    task_id: str = Path(..., description="Task ID to get statistics for"),
    current_user = Depends(require_user)
):
    """
    📊 Get statistics for a specific task
    
    Returns basic statistics about the dataset for the specified task.
    """
    try:
        # Get basic stats
        columns_info = await matching_service.get_available_columns(task_id)
        
        return {
            "task_id": task_id,
            "total_records": columns_info.total_records,
            "total_columns": 0,
            "recommended_columns": columns_info.recommended_columns,
            "status": "ready_for_matching"
        }
    except TaskException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")