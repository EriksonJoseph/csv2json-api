from fastapi import APIRouter, Query, Path, Depends, HTTPException
from app.routers.user.user_service import UserService
from app.routers.user.user_model import UserCreate, UserUpdate, ChangePasswordRequest, VerifyEmailRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.utils.advanced_performance import tracker
from app.dependencies.auth import require_admin, require_user, get_current_user
from bson import ObjectId # type: ignore
from app.api.schemas import PaginationResponse
from typing import Dict, Any, Optional

router = APIRouter(
    prefix="/user",
    tags=["users"],
    responses={404: {"description": "Not Found"}}
)

# Initialize service
user_service = UserService()

@router.post("/")
@tracker.measure_async_time
async def create_user(user: UserCreate, current_user: Any = Depends(require_admin)) -> Dict[str, Any]:
    """
    📋 สร้างผู้ใช้ใหม่ (เฉพาะ Admin)
    """
    return await user_service.create_user(user, current_user.user_id)

@router.patch("/{user_id}")
@tracker.measure_async_time
async def update_user(user_id: str, user_update: UserUpdate, current_user: Any = Depends(require_user)) -> Dict[str, Any]:
    """
    อัปเดตข้อมูลผู้ใช้ (Admin สามารถแก้ไขทุกคน, User สามารถแก้ไขตัวเองได้)
    """
    # Check permissions: Admin can update anyone, users can only update themselves
    if current_user.user_id != user_id and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    result = await user_service.update_user(user_id, user_update, current_user.user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return {"message": "User updated successfully"}

@router.get("/{user_id}")
@tracker.measure_async_time
async def get_user(
    user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการดึงข้อมูล"),
    current_user: Any = Depends(require_user)
) -> Dict[str, Any]:
    """
    ดึงข้อมูลผู้ใช้ตาม ID
    """
    # Users can only view their own data, admins can view all
    if current_user.user_id != user_id and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return await user_service.get_user(user_id)

@router.get("/", response_model=PaginationResponse[Dict[str, Any]])
@tracker.measure_async_time
async def get_all_users(
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1, le=100),
    current_user: Any = Depends(require_user)
) -> Dict[str, Any]:
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
                "list": [user],
                "total": 1,
                "page": page,
                "limit": limit
            }
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/{user_id}")
@tracker.measure_async_time
async def delete_user(user_id: str = Path(..., description="ID ของผู้ใช้ที่ต้องการลบ"), current_user: Any = Depends(require_admin)) -> Dict[str, Any]:
    """
    ลบผู้ใช้ (เฉพาะ Admin)
    """
    # Validate user_id
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Check if user exists
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="🔍 ไม่พบผู้ใช้ที่ต้องการลบ")
    
    # Delete user
    # Note: We need to add delete_user method to UserService
    from app.database import get_collection
    from app.utils.serializers import individual_serial
    
    users_collection = await get_collection("users")
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    
    # Check if delete was successful
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="⚠️ เกิดข้อผิดพลาดในการลบข้อมูล")
    
    # Return deleted user data
    return {
        "message": "🗑️ ลบข้อมูลผู้ใช้สำเร็จ",
        "deleted_user": individual_serial(user)
    }

@router.post("/verify-email")
@tracker.measure_async_time
async def verify_email(verify_request: VerifyEmailRequest) -> Dict[str, Any]:
    """
    ✅ Verify user email address and set password using token
    """
    return await user_service.verify_email_with_password(verify_request)

@router.post("/{user_id}/resend-verification")
@tracker.measure_async_time
async def resend_verification_email(user_id: str, current_user: Any = Depends(require_admin)) -> Dict[str, Any]:
    """
    📧 Resend email verification (Admin only)
    """
    return await user_service.resend_verification_email(user_id)

@router.post("/forgot-password")
@tracker.measure_async_time
async def forgot_password(request: ForgotPasswordRequest) -> Dict[str, Any]:
    """
    🔐 Send password reset email
    """
    return await user_service.forgot_password(request)

@router.post("/reset-password")
@tracker.measure_async_time
async def reset_password(request: ResetPasswordRequest) -> Dict[str, Any]:
    """
    🔄 Reset password using token
    """
    return await user_service.reset_password(request)
