from fastapi import APIRouter, Query, Path
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserUpdate
from app.utils.advanced_performance import tracker

router = APIRouter(
    prefix="/user",
    tags=["users"],
    responses={404: {"description": "Not Found"}}
)

# Initialize repository and service
user_repository = UserRepository()
user_service = UserService(user_repository)

@router.post("/")
@tracker.measure_async_time
async def create_user(user: UserCreate):
    """
    📋 สร้างผู้ใช้ใหม่
    """
    return await user_service.create_user(user)

@router.patch("/{user_id}")
@tracker.measure_async_time
async def update_user(user_id: str, user_update: UserUpdate):
    """
    🔄 อัปเดตข้อมูลผู้ใช้
    """
    return await user_service.update_user(user_id, user_update)

@router.get("/{user_id}")
@tracker.measure_async_time
async def get_user(user_id: str):
    """
    📋 ดึงข้อมูลผู้ใช้ตาม ID
    """
    return await user_service.get_user(user_id)

@router.get("/")
@tracker.measure_async_time
async def get_all_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    📋 ดึงรายการผู้ใช้ทั้งหมด
    """
    return await user_service.get_all_users(page, limit)
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