from fastapi import APIRouter
from app.database import get_database

router = APIRouter(
  prefix="/user",
  tags=["users"],
  responses={404: { "description": "Not Found"}}
)

@router.get("/")
async def get_users():
   # เชื่อมต่อกับ MongoDB และดึงรายชื่อ collections ทั้งหมด
  db = get_database()
  collections = db.list_collection_names()
  
  # ส่งคืนข้อมูลพร้อม message
  return {
    "message": "📊 Collections in Database",
    "collections": collections
  }