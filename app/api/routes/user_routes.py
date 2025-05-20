from fastapi import APIRouter, Depends, HTTPException, Path, Query
from app.api.schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from app.api.schemas.response_schemas import ResponseModel, PaginatedResponse
from app.services.user_service import UserService
from app.api.dependencies import get_user_repository
from app.utils.advanced_performance import tracker
from bson import ObjectId
from typing import List

router = APIRouter(
    prefix="/user",
    tags=["users"],
    responses={404: {"description": "Not Found"}}
)

@router.post("/", response_model=ResponseModel[UserResponse])
@tracker.measure_async_time
async def create_user(
    user: UserCreate,
    user_service: UserService = Depends(lambda: UserService(get_user_repository()))
):
    """
    👤 สร้างผู้ใช้ใหม่
    """
    result = await user_service.create_user(user)
    return ResponseModel(
        message="✅ สร้างผู้ใช้สำเร็จ",
        data=result
    )

@router.patch("/{user_id}", response_model=ResponseModel[UserResponse])
@tracker.measure_async_time
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    user_service: UserService = Depends(lambda: UserService(get_user_repository()))
):
    """
    ✏️ อัปเดตข้อมูลผู้ใช้
    """
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    result = await user_service.update_user(user_id, user_update)
    return result

@router.get("/", response_model=PaginatedResponse[List[UserResponse]])
@tracker.measure_async_time
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_service: UserService = Depends(lambda: UserService(get_user_repository()))
):
    """
    👥 ดึงรายการผู้ใช้ทั้งหมด
    """
    result = await user_service.get_all_users(page, limit)
    return result

@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
@tracker.measure_async_time
async def get_user(
    user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการดึงข้อมูล"),
    user_service: UserService = Depends(lambda: UserService(get_user_repository()))
):
    """
    👤 ดึงข้อมูลผู้ใช้ตาม ID
    """
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    result = await user_service.get_user(user_id)
    return result

@router.delete("/{user_id}", response_model=ResponseModel[UserResponse])
@tracker.measure_async_time
async def delete_user(
    user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการลบ"),
    user_service: UserService = Depends(lambda: UserService(get_user_repository()))
):
    """
    🗑️ ลบผู้ใช้ตาม ID
    """
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    result = await user_service.delete_user(user_id)
    return result