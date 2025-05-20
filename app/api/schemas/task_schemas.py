# app/api/schemas/task_schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TaskBase(BaseModel):
    """
    ข้อมูลพื้นฐานของงาน
    """
    topic: str
    references: str
    file_id: str

class TaskCreate(TaskBase):
    """
    ข้อมูลสำหรับสร้างงานใหม่
    """
    created_file_date: str  # Format: "YYYY-MM-DD"
    updated_file_date: str  # Format: "YYYY-MM-DD"

class TaskUpdate(BaseModel):
    """
    ข้อมูลสำหรับอัปเดตงาน
    """
    topic: Optional[str] = None
    created_file_date: Optional[str] = None  # Format: "YYYY-MM-DD"
    updated_file_date: Optional[str] = None  # Format: "YYYY-MM-DD"
    references: Optional[str] = None
    file_id: Optional[str] = None
    is_done_created_doc: Optional[bool] = None
    column_names: Optional[List[str]] = None
    error_message: Optional[str] = None

class TaskResponse(TaskBase):
    """
    ข้อมูลงานสำหรับส่งกลับไปยังผู้ใช้งาน
    """
    id: str
    created_file_date: str
    updated_file_date: str
    is_done_created_doc: bool
    column_names: List[str]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True