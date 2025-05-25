from fastapi import APIRouter, Query, Path, Depends
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserUpdate
from app.utils.advanced_performance import tracker
from app.dependencies.auth import require_admin, require_user, get_current_user

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
async def create_user(user: UserCreate, current_user = Depends(require_admin)):
    """
    📋 สร้างผู้ใช้ใหม่ (เฉพาะ Admin)
    """
    return await user_service.create_user(user, current_user)

@router.patch("/{user_id}")
@tracker.measure_async_time
async def update_user(user_id: str, user_update: UserUpdate, current_user = Depends(require_admin)):
    """
    อัปเดตข้อมูลผู้ใช้ (เฉพาะ Admin)
    """
    return await user_service.update_user(user_id, user_update, current_user)

@router.get("/{user_id}")
@tracker.measure_async_time
async def get_user(
    user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการดึงข้อมูล"),
    current_user = Depends(require_user)
):
    """
    ดึงข้อมูลผู้ใช้ตาม ID
    """
    # Users can only view their own data, admins can view all
    if current_user.user_id != user_id and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return await user_service.get_user(user_id)

@router.get("/")
@tracker.measure_async_time
async def get_all_users(
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(require_user)
):
    """
    ดึงรายการผู้ใช้
    - Admin: ดูได้ทุกคน
    - User: ดูได้เฉพาะตัวเอง
    """
    if "admin" in current_user.roles:
        return await user_service.get_all_users(page, limit)
    else:
        # Users can only view their own data
        user = await user_service.get_user(current_user.user_id)
        if user:
            return {
                "message": "👤 ข้อมูลผู้ใช้",
                "users": [user]
            }
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/{user_id}")
@tracker.measure_async_time
async def delete_user(user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการลบ"), current_user = Depends(require_admin)):
    """
    ลบผู้ใช้ (เฉพาะ Admin)
    """
    return await user_service.delete_user(user_id)
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