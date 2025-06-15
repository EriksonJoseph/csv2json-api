from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, Any
from app.api.schemas.pagination import PaginationResponse
from app.routers.search.search_service import SearchService
from app.routers.search.search_model import AdvancedSearchRequest
from app.dependencies.auth import require_user
from app.utils.advanced_performance import tracker
from app.exceptions import TaskException

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not Found"}}
)

# Initialize service
search_service = SearchService()

@router.post("/", response_model=str)
@tracker.measure_async_time
async def create_search(
    request: AdvancedSearchRequest,
    current_user: Any = Depends(require_user)
) -> str:
    """
    🔍 Create search with configurable matching options
    
    This endpoint performs advanced search with configurable matching options for each column:
    - whole_word: Match complete words only
    - match_case: Case-sensitive matching  
    - match_length: Match exact length
    
    **Example Request:**
    ```json
    {
        "task_id": "65f1b2c3d4e5f6789abcdef0",
        "column_names": ["Naal_firstname", "Naal_middlename", "Naal_lastname"],
        "column_options": {
            "Naal_firstname": {
                "whole_word": true,
                "match_case": false,
                "match_length": false
            },
            "Naal_middlename": {
                "whole_word": false,
                "match_case": true,
                "match_length": true
            },
            "Naal_lastname": {
                "whole_word": true,
                "match_case": false,
                "match_length": false
            }
        },
        "list": [
            {
                "no": 1,
                "Naal_firstname": "Justin",
                "Naal_middlename": "Timber",
                "Naal_lastname": "Lee"
            },
            {
                "no": 2,
                "Naal_firstname": "dsajfkj",
                "Naal_middlename": "jfkdlsf",
                "Naal_lastname": "fdksajf"
            }
        ]
    }
    ```
    """
    try:
        return await search_service.create_search(request, current_user.user_id)
    except TaskException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/history", response_model=PaginationResponse[Dict[str, Any]])
@tracker.measure_async_time
async def get_search_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: Any = Depends(require_user)
) -> Dict[str, Any]:
    """
    📜 Get search history for the current user
    
    Returns a paginated list of previous searches performed by the current user.
    """
    try:
        history_data = await search_service.get_search_history(
            current_user.user_id, page, limit
        )
        return history_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/result/{search_id}")
@tracker.measure_async_time
async def get_search_result(
    search_id: str = Path(..., description="Search ID to get search result for"),
    current_user: Any = Depends(require_user)
) -> Dict[str, Any]:
    """
    📊 Get search result for a specific search history
    
    Returns the detailed search result from search_history collection
    including all search parameters, execution details, and summary statistics.
    """
    try:
        return await search_service.get_search_result(search_id)
    except TaskException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.get("/health")
@tracker.measure_async_time
async def health_check(current_user: Any = Depends(require_user)) -> Dict[str, Any]:
    """
    🏥 Health check for search service
    """
    return {
        "status": "healthy",
        "service": "search",
        "message": "Search service is operational",
        "user": current_user.user_id
    }
