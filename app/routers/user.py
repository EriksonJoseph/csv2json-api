from fastapi import APIRouter, Query
from app.database import get_collection
from bson import ObjectId
from typing import List, Dict, Any

router = APIRouter(
  prefix="/user",
  tags=["users"],
  responses={404: { "description": "Not Found"}}
)

@router.get("/")
async def get_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
  # เชื่อมต่อกับ collection users
  users_collection = get_collection("users")
  
  # คำนวณ skip สำหรับ pagination
  skip = (page - 1) * limit
  
  # นับจำนวน users ทั้งหมด
  total_users = await users_collection.count_documents({})
  
  # ดึงข้อมูลแบบ pagination
  users_cursor = users_collection.find().skip(skip).limit(limit)
  users = await users_cursor.to_list(length=limit)
  
  # แปลง ObjectId เป็น string เพื่อให้สามารถ serialize เป็น JSON ได้
  for user in users:
    if "_id" in user:
      user["_id"] = str(user["_id"])
  
  # ส่งคืนข้อมูลพร้อม metadata สำหรับ pagination
  return {
    "message": "👤 รายชื่อผู้ใช้ทั้งหมด",
    "total": total_users,
    "page": page,
    "limit": limit,
    "pages": (total_users + limit - 1) // limit,  # จำนวนหน้าทั้งหมด
    "users": users
  }