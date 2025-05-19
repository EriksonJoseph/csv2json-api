from pydantic import BaseModel

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