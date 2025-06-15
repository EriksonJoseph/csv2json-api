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

class ColumnOptions(BaseModel):
    whole_word: bool = Field(default=False, description="Match whole words only")
    match_case: bool = Field(default=False, description="Case-sensitive matching")
    match_length: bool = Field(default=False, description="Match exact length")

class SearchQueryRow(BaseModel):
    no: int
    additional_properties: Dict[str, str] = Field(default_factory=dict)
    
    def __init__(self, **data):
        no = data.pop('no', 0)
        super().__init__(no=no, additional_properties=data)
    
    def __getitem__(self, key: str) -> str:
        if key == 'no':
            return str(self.no)
        return self.additional_properties.get(key, "")
    
    def get(self, key: str, default: str = "") -> str:
        if key == 'no':
            return str(self.no)
        return self.additional_properties.get(key, default)

class AdvancedSearchRequest(BaseModel):
    task_id: str
    column_names: List[str] = Field(description="List of column names to search")
    column_options: Dict[str, ColumnOptions] = Field(description="Search options for each column")
    list: List[Dict[str, str]] = Field(description="List of search queries with column values")

class ColumnResult(BaseModel):
    found: bool = Field(description="Whether any matches were found")
    count: int = Field(description="Number of matching rows")
    search_term: str = Field(description="The search term used")

class AdvancedSearchQueryResult(BaseModel):
    query_no: int = Field(description="Query number from input")
    query_name: str = Field(description="Combined name from all columns")
    column_results: Dict[str, ColumnResult] = Field(description="Results for each column")
