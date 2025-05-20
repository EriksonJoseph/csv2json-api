from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TaskCreate(BaseModel):
    topic: str
    created_file_date: str  # Format: "YYYY-MM-DD"
    updated_file_date: str  # Format: "YYYY-MM-DD"
    references: str
    file_id: str

class TaskUpdate(BaseModel):
    topic: Optional[str] = None
    created_file_date: Optional[str] = None  # Format: "YYYY-MM-DD"
    updated_file_date: Optional[str] = None  # Format: "YYYY-MM-DD"
    references: Optional[str] = None
    file_id: Optional[str] = None
    is_done_created_doc: Optional[bool] = None
    column_names: Optional[List[str]] = None
    error_message: Optional[str] = None