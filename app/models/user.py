"""
User Model

นิยามโครงสร้างข้อมูลของผู้ใช้
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

class User:
    def __init__(
        self,
        username: str,
        password: str,
        email: str = "",
        first_name: str = "",
        last_name: str = "",
        middle_name: str = "",
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.username = username
        self.password = password
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.id = id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        สร้างอ็อบเจ็กต์ User จาก dictionary
        """
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            email=data.get("email", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            middle_name=data.get("middle_name", ""),
            id=str(data.get("_id", "")),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self, exclude_password: bool = True) -> Dict[str, Any]:
        """
        แปลงอ็อบเจ็กต์ User เป็น dictionary
        """
        result = {
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if self.id:
            result["_id"] = self.id
        
        if not exclude_password:
            result["password"] = self.password
        
        return result