"""
Task Model

นิยามโครงสร้างข้อมูลของงาน
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

class Task:
    def __init__(
        self,
        topic: str,
        references: str,
        file_id: str,
        created_file_date: str,
        updated_file_date: str,
        is_done_created_doc: bool = False,
        column_names: Optional[List[str]] = None,
        error_message: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.topic = topic
        self.references = references
        self.file_id = file_id
        self.created_file_date = created_file_date
        self.updated_file_date = updated_file_date
        self.is_done_created_doc = is_done_created_doc
        self.column_names = column_names or []
        self.error_message = error_message
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """
        สร้างอ็อบเจ็กต์ Task จาก dictionary
        """
        # แปลง datetime เป็น string ถ้าจำเป็น
        created_file_date = data.get("created_file_date")
        if isinstance(created_file_date, datetime):
            created_file_date = created_file_date.strftime("%Y-%m-%d")
            
        updated_file_date = data.get("updated_file_date")
        if isinstance(updated_file_date, datetime):
            updated_file_date = updated_file_date.strftime("%Y-%m-%d")
            
        return cls(
            topic=data.get("topic", ""),
            references=data.get("references", ""),
            file_id=data.get("file_id", ""),
            created_file_date=created_file_date or "",
            updated_file_date=updated_file_date or "",
            is_done_created_doc=data.get("is_done_created_doc", False),
            column_names=data.get("column_names", []),
            error_message=data.get("error_message"),
            id=str(data.get("_id", "")),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        แปลงอ็อบเจ็กต์ Task เป็น dictionary
        """
        result = {
            "topic": self.topic,
            "references": self.references,
            "file_id": self.file_id,
            "created_file_date": self.created_file_date,
            "updated_file_date": self.updated_file_date,
            "is_done_created_doc": self.is_done_created_doc,
            "column_names": self.column_names,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if self.id:
            result["_id"] = self.id
        
        return result