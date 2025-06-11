from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.routers.auth.auth_model import UserRole

class User(BaseModel):
    _id: str
    username: str
    first_name: str
    middle_name: str
    last_name: str
    email: str
    roles: List[UserRole] = [UserRole.USER]
    is_active: bool = True
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    login_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""
    roles: List[UserRole] = [UserRole.USER]

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
