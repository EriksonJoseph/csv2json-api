from pydantic import BaseModel
from typing import List, TypeVar, Generic

T = TypeVar('T')

class PaginationResponse(BaseModel, Generic[T]):
    """
    Standardized pagination response format
    
    Structure:
    {
        "list": [...],     # Array of items
        "total": 299,      # Total number of items
        "page": 1,         # Current page number
        "limit": 10        # Items per page limit
    }
    """
    list: List[T]
    total: int
    page: int
    limit: int