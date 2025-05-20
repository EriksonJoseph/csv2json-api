# app/api/schemas/user_schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """
    ข้อมูลพื้นฐานของผู้ใช้
    """
    username: str
    email: Optional[str] = ""
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    middle_name: Optional[str] = ""

class UserCreate(UserBase):
    """
    ข้อมูลสำหรับสร้างผู้ใช้ใหม่
    """
    password: str

class UserUpdate(BaseModel):
    """
    ข้อมูลสำหรับอัปเดตผู้ใช้
    """
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None

class UserResponse(UserBase):
    """
    ข้อมูลผู้ใช้สำหรับส่งกลับไปยังผู้ใช้งาน
    """
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True