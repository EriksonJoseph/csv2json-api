from fastapi import APIRouter, Depends, Request
from app.models.auth import UserLogin, Token
from app.models.user import UserCreate
from app.dependencies.auth import auth_service, get_current_user, require_admin
from app.utils.advanced_performance import tracker
from typing import Dict

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)

@router.post("/login", response_model=Token)
@tracker.measure_async_time
async def login(request: Request, user_login: UserLogin):
    """
    🔐 Login
    """
    # Get client IP address
    ip_address = request.client.host
    
    return await auth_service.login(user_login, ip_address)

@router.get("/login_history/{user_id}", response_model=Dict)
@tracker.measure_async_time
async def get_login_history(user_id: str, current_user = Depends(require_admin)):
    """
    📋 ดูประวัติการเข้าสู่ระบบ (เฉพาะ Admin)
    """
    history = await auth_service.get_login_history(user_id)
    return history.dict() if history else {}

@router.post("/register", response_model=dict)
@tracker.measure_async_time
async def register(user: UserCreate):
    """
    📝 Register new user
    """
    return await auth_service.register(user)

@router.get("/me")
@tracker.measure_async_time
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    👤 Get current user info
    """
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "roles": current_user.roles
    }

@router.post("/unlock/{user_id}")
@tracker.measure_async_time
async def unlock_user(user_id: str, current_user = Depends(require_admin)):
    """
    🔓 Unlock user account (Admin only)
    
    This will reset the login attempts counter for the specified user.
    """
    success = await auth_service.unlock_user(user_id)
    if not success:
        return {"status": "error", "message": "Failed to unlock user"}
    return {"status": "success", "message": "User unlocked successfully"}
