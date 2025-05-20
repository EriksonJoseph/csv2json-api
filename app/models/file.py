from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FileInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    upload_date: datetime
    metadata: Optional[dict] = None