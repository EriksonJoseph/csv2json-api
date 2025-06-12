from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UploadStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class FileInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    upload_date: datetime
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class ChunkedUpload(BaseModel):
    upload_id: str
    original_filename: str
    total_chunks: int
    chunk_size: int
    total_size: int
    mime_type: str
    status: UploadStatus
    received_chunks: List[int]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class ChunkUploadRequest(BaseModel):
    upload_id: str
    chunk_number: int
    total_chunks: int
    is_last_chunk: bool = False

class InitiateUploadRequest(BaseModel):
    filename: str
    total_size: int
    chunk_size: int
    mime_type: str
