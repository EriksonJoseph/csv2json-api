from fastapi import APIRouter, Query
from app.database import get_collection
from app.schema.schemas import list_serial
from bson import ObjectId
from typing import List, Dict, Any
import pprint

router = APIRouter(
  prefix="/user",
  tags=["users"],
  responses={404: { "description": "Not Found"}}
)

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