from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class FileResponse(BaseModel):
    """
    ข้อมูลไฟล์สำหรับส่งกลับไปยังผู้ใช้งาน
    """
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    file_extension: str
    upload_date: datetime
    metadata: Optional[Dict[str, Any]] = {}

    class Config:
        orm_mode = True