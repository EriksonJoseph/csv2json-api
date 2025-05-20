from fastapi import APIRouter, Query, HTTPException, Path
from app.database import get_collection
from app.schema.schemas import list_serial, individual_serial
from app.models.user import UserCreate
from bson import ObjectId
import pprint
from datetime import datetime
from app.models.user import UserCreate, UserUpdate
from app.utils.performance import measure_async_time
from app.utils.advanced_performance import tracker, TimedBlock

router = APIRouter(
  prefix="/user",
  tags=["users"],
  responses={404: { "description": "Not Found"}}
)

@router.post("/")
@tracker.measure_async_time
async def create_user(user: UserCreate):
    # เชื่อมต่อกับ collection users
    users_collection = await get_collection("users")
    
    # ตรวจสอบว่า username ซ้ำหรือไม่
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="👎 Username นี้มีอยู่ในระบบแล้ว")
    
    existing_user = await users_collection.find_one({"email": user.email})
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
    result = await users_collection.insert_one(user_data)
    
    # ดึงข้อมูลที่บันทึกแล้วกลับมาเพื่อส่งคืน
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    
    # แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสม
    return {
        "message": "✅ สร้างผู้ใช้สำเร็จ",
        "user": individual_serial(created_user)
    }

@router.patch("/{user_id}")
@tracker.measure_async_time
async def update_user(user_id: str, user_update: UserUpdate):
    # เชื่อมต่อกับ collection users
    users_collection = await get_collection("users")

    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    # ตรวจสอบว่าผู้ใช้มีอยู่หรือไม่
    existing_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="🔍 ไม่พบผู้ใช้ที่ต้องการอัปเดต")
    
    # สร้าง dict สำหรับเก็บข้อมูลที่จะอัปเดต
    update_data = {}
    
    # เพิ่มเฉพาะฟิลด์ที่ไม่ใช่ None ลงใน update_data
    user_dict = user_update.dict(exclude_unset=True)
    for field, value in user_dict.items():
        if value is not None:
            update_data[field] = value
    
    # ถ้ามีการอัปเดต username ให้ตรวจสอบว่าซ้ำหรือไม่
    if "username" in update_data:
        username_check = users_collection.find_one({
            "username": update_data["username"],
            "_id": {"$ne": ObjectId(user_id)}  # ไม่เป็นผู้ใช้ปัจจุบัน
        })
        if username_check:
            raise HTTPException(status_code=400, detail="👎 Username นี้มีอยู่ในระบบแล้ว")
    
    # ถ้าไม่มีข้อมูลที่จะอัปเดตให้แจ้งเตือน
    if not update_data:
        raise HTTPException(status_code=400, detail="⚠️ ไม่มีข้อมูลที่จะอัปเดต")
    
    # เพิ่ม timestamp สำหรับการอัปเดต
    update_data["updated_at"] = datetime.now()
    
    # อัปเดตข้อมูลใน MongoDB
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # ตรวจสอบว่าอัปเดตสำเร็จหรือไม่
    if result.modified_count == 0:
        # ข้อมูลไม่มีการเปลี่ยนแปลง
        return {
            "message": "ℹ️ ไม่มีการเปลี่ยนแปลงข้อมูล",
            "user": individual_serial(existing_user)
        }
    
    # ดึงข้อมูลที่อัปเดตแล้ว
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    # ส่งข้อมูลที่อัปเดตแล้วกลับไป
    return {
        "message": "✅ อัปเดตข้อมูลผู้ใช้สำเร็จ",
        "user": individual_serial(updated_user)
    }

@router.get("/")
@tracker.measure_async_time
async def get_all_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
  # เชื่อมต่อกับ collection users
  users_collection = await get_collection("users")
  # คำนวณ skip สำหรับ pagination
  skip = (page - 1) * limit
  
  # นับจำนวน users ทั้งหมด (ใช้ await กับ Motor)
  total_users = await users_collection.count_documents({})
  
  # ดึงข้อมูลโดยมีการทำ pagiantion
  cursor = users_collection.find().skip(skip).limit(limit)
  users_list = await cursor.to_list(length=limit)
  users = list_serial(users_list)

  # ส่งคืนข้อมูลพร้อม metadata สำหรับ pagination
  return {
    "message": "👤 รายชื่อผู้ใช้ทั้งหมด",
    "total": total_users,
    "page": page,
    "limit": limit,
    "pages": (total_users + limit - 1) // limit,
    "users": users
  }

@router.get("/{user_id}")
@tracker.measure_async_time
async def get_user(user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการดึงข้อมูล")):
    # เชื่อมต่อกับ collection users
    users_collection = await get_collection("users")

    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    # ดึงข้อมูลผู้ใช้จาก MongoDB
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    pprint.pp(user)
    
    # ตรวจสอบว่าพบผู้ใช้หรือไม่
    if not user:
        raise HTTPException(status_code=404, detail="🔍 ไม่พบผู้ใช้ที่ต้องการ")
    
    # แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสมและส่งกลับ
    return {
        "message": "👤 ข้อมูลผู้ใช้",
        "user": individual_serial(user)
    }

@router.delete("/{user_id}")
@tracker.measure_async_time
async def delete_user(user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการลบ")):
    # เชื่อมต่อกับ collection users
    users_collection = await get_collection("users")
    
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    # หาข้อมูลผู้ใช้ก่อนลบเพื่อเก็บไว้แสดงผล
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    # ตรวจสอบว่าพบผู้ใช้หรือไม่
    if not user:
        raise HTTPException(status_code=404, detail="🔍 ไม่พบผู้ใช้ที่ต้องการลบ")
    
    # ลบข้อมูลผู้ใช้จาก MongoDB
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    
    # ตรวจสอบว่าลบสำเร็จหรือไม่
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="⚠️ เกิดข้อผิดพลาดในการลบข้อมูล")
    
    # แปลงข้อมูลที่ถูกลบและส่งกลับ
    return {
        "message": "🗑️ ลบข้อมูลผู้ใช้สำเร็จ",
        "deleted_user": individual_serial(user)
    }