from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId # type: ignore
from datetime import datetime

# Custom field for handling ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# Watchlist model for request validation
class WatchlistModel(BaseModel):
    title: str
    list: List[str] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Watchlist response model
class WatchlistResponse(WatchlistModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    total_names: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "_id": "60d21b4967d0d1d8ef43e111",
                "title": "My Watchlist",
                "list": ["item1", "item2", "item3"],
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }


# Update model
class WatchlistUpdate(BaseModel):
    title: Optional[str] = None
    list: Optional[List[str]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Paginated response model
class WatchlistPaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    list: List[dict]
    
    class Config:
        schema_extra = {
            "example": {
                "total": 2,
                "page": 1,
                "per_page": 10,
                "total_pages": 1,
                "list": [
                    {
                        "_id": "60d21b4967d0d1d8ef43e111",
                        "title": "My Watchlist",
                        "list": ["item1", "item2", "item3"]
                    }
                ]
            }
        }
