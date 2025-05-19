from fastapi import APIRouter, Query, HTTPException
from app.database import get_collection
from app.schema.schemas import list_serial, individual_serial
from app.models.user import UserCreate
from bson import ObjectId
from typing import List, Dict, Any
import pprint
from datetime import datetime

router = APIRouter(
  prefix="/user",
  tags=["users"],
  responses={404: { "description": "Not Found"}}
)

# เพิ่ม endpoint POST สำหรับสร้างผู้ใช้ใหม่
@router.post("/")
async def create_user(user: UserCreate):
    pprint.pp(user)

    # เชื่อมต่อกับ collection users
    users_collection = get_collection("users")
    
    # ตรวจสอบว่า username ซ้ำหรือไม่
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="👎 Username นี้มีอยู่ในระบบแล้ว")
    
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="👎 Email นี้มีอยู่ในระบบแล้ว")
    
    # เตรียมข้อมูลสำหรับบันทึก
    current_time = datetime.now()
    user_data = {
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "middle_name": user.middle_name,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    # บันทึกข้อมูลลงใน MongoDB
    result = users_collection.insert_one(user_data)
    
    # ดึงข้อมูลที่บันทึกแล้วกลับมาเพื่อส่งคืน
    created_user = users_collection.find_one({"_id": result.inserted_id})
    
    # แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสม
    return {
        "message": "✅ สร้างผู้ใช้สำเร็จ",
        "user": individual_serial(created_user)
    }

@router.get("/")
async def get_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
  print(f"page: {page} | limit: {limit}")
  # เชื่อมต่อกับ collection users
  users_collection = get_collection("users")
  
  # คำนวณ skip สำหรับ pagination
  skip = (page - 1) * limit
  
  # นับจำนวน users ทั้งหมด (ใช้ await กับ Motor)
  total_users = users_collection.count_documents({})
  
  # ดึงข้อมูลโดยมีการทำ pagiantion
  users = list_serial(users_collection.find().skip(skip).limit(limit))

  # ส่งคืนข้อมูลพร้อม metadata สำหรับ pagination
  return {
    "message": "👤 รายชื่อผู้ใช้ทั้งหมด",
    "total": total_users,
    "page": page,
    "limit": limit,
    "pages": (total_users + limit - 1) // limit,
    "users": users
  }