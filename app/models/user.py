from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
  _id: str
  username: str
  first_name: str
  middle_name: str
  email: str

# เพิ่ม model สำหรับการสร้างผู้ใช้ใหม่
class UserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""

# เพิ่ม model สำหรับการอัปเดตผู้ใช้ (ทุกฟิลด์เป็น Optional)
class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None