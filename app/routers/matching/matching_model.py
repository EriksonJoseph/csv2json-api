from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SingleSearchRequest(BaseModel):
    task_id: str
    name: str
    threshold: int = Field(default=70, ge=1, le=100, description="Matching threshold percentage (1-100)")
    columns: List[str] = Field(description="List of column names to search in")

class BulkSearchRequest(BaseModel):
    task_id: str
    threshold: int = Field(default=70, ge=1, le=100, description="Matching threshold percentage (1-100)")
    columns: List[str] = Field(description="List of column names to search in")
    list: List[str] = Field(description="List of names to search for")
    watchlist_id: Optional[str] = Field(default=None, description="Optional watchlist ID to associate with this search")

class MatchedRecord(BaseModel):
    query_name: str = Field(description="The search query name that was used")
    confidence: float = Field(description="Confidence score (0-100)")
    matched_column: str = Field(description="Column name where match was found")
    matched_value: str = Field(description="Actual value that matched")
    entity_id: Optional[str] = Field(description="Entity ID from the sanctions list")
    full_record: Optional[Dict[str, Any]] = Field(description="Complete record from database")

class SingleSearchResponse(BaseModel):
    name: str
    matched: float = Field(description="Best match confidence score")
    found: bool = Field(description="Whether any match above threshold was found")
    total_rows: int = Field(default=0, description="Search from total rows")
    execution_time_ms: float = Field(default=0.0, description="Totla executed time")
    matched_records: List[MatchedRecord] = Field(default_factory=list)
    search_id: str = Field(description="MongoDB ObjectId of saved search history")
    status: Optional[str] = Field(default="completed", description="Search status: pending, processing, completed, failed")

class BulkSearchItem(BaseModel):
    name: str
    matched: float = Field(description="Best match confidence score")
    found: bool = Field(description="Whether any match above threshold was found")
    best_match: Optional[MatchedRecord] = None

class BulkSearchResponse(BaseModel):
    results: List[BulkSearchItem]
    summary: Dict[str, Any] = Field(description="Summary statistics of the search")
    search_id: str = Field(description="MongoDB ObjectId of saved search history")

class AvailableColumnsResponse(BaseModel):
    task_id: str
    columns: List[str] = Field(description="All available columns in the dataset")
    recommended_columns: List[str] = Field(description="Recommended columns for name matching")
    total_records: int = Field(description="Total number of records in the dataset")

class SearchHistoryItem(BaseModel):
    _id: str
    search_id: str
    task_id: str
    search_type: str = Field(description="single or bulk")
    query_names: List[str]
    columns_used: List[str]
    threshold_used: int
    results_found: int
    total_searched: int
    execution_time_ms: float = Field(description="Execution time in milliseconds")
    total_rows: int = Field(description="Total rows in the dataset")
    watchlist_id: Optional[str] = Field(default=None, description="Associated watchlist ID if applicable")
    status: str = Field(default="completed", description="Search status: pending, processing, completed, failed")
    created_at: datetime
    created_by: str = Field(description="User ID who performed the search")
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

class SearchHistoryResponse(BaseModel):
    list: List[SearchHistoryItem]
    total: int
    page: int
    limit: int