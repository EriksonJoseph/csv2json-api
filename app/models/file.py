"""
File Model

นิยามโครงสร้างข้อมูลของไฟล์
"""
from datetime import datetime
from typing import Optional, Dict, Any

class File:
    def __init__(
        self,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        file_extension: str,
        id: Optional[str] = None,
        upload_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.file_extension = file_extension
        self.upload_date = upload_date or datetime.now()
        self.metadata = metadata or {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "File":
        """
        สร้างอ็อบเจ็กต์ File จาก dictionary
        """
        return cls(
            filename=data.get("filename", ""),
            original_filename=data.get("original_filename", ""),
            file_path=data.get("file_path", ""),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type", ""),
            file_extension=data.get("file_extension", ""),
            id=str(data.get("_id", "")),
            upload_date=data.get("upload_date"),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        แปลงอ็อบเจ็กต์ File เป็น dictionary
        """
        result = {
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_extension": self.file_extension,
            "upload_date": self.upload_date,
            "metadata": self.metadata
        }
        
        if self.id:
            result["_id"] = self.id
        
        return result