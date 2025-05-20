from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Any

# Generic type for response data
T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    """
    รูปแบบการตอบกลับทั่วไปของ API
    """
    message: str
    success: bool = True
    data: Optional[T] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """
    รูปแบบการตอบกลับแบบแบ่งหน้า
    """
    message: str
    success: bool = True
    total: int
    page: int
    limit: int
    pages: int
    data: T