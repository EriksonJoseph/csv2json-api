from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Dict, Any
from app.routers.auth.auth_model import UserLogin, Token, RefreshTokenRequest
from app.routers.user.user_model import UserCreate, ChangePasswordRequest
from app.dependencies.auth import get_current_user, require_admin, require_user
from app.utils.advanced_performance import tracker
from app.routers.auth.auth_service import AuthService
from app.routers.user.user_service import UserService
import pprint

# Create a router instance
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Create instance of AuthService
auth_service = AuthService()
# Create instance of UserService
user_service = UserService()

@router.post("/login", response_model=Token)
@tracker.measure_async_time
async def login(request: Request, user_login: UserLogin) -> Token:
    """
    🔐 Login
    """
    # Get client IP address
    ip_address = request.client.host if request.client else "unknown"
    # Get user agent if available
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.login(user_login, ip_address, user_agent)

@router.get("/login_history/{user_id}", response_model=Dict)
@tracker.measure_async_time
async def get_login_history(user_id: str, current_user: Any = Depends(require_admin)) -> Dict[str, Any]:
    """
    📋 ดูประวัติการเข้าสู่ระบบ (เฉพาะ Admin)
    """
    history = await auth_service.get_login_history(user_id)
    return history.dict() if history else {}

@router.post("/register", response_model=dict)
@tracker.measure_async_time
async def register(user: UserCreate) -> Dict[str, Any]:
    """
    📝 Register new user
    """
    return await auth_service.register(user)

@router.get("/me")
@tracker.measure_async_time
async def get_current_user_info(current_user: Any = Depends(get_current_user)) -> Dict[str, Any]:
    """
    👤 Get current user info
    """
    user = await user_service.get_user(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Not found user")
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "roles": current_user.roles,
        "first_name": user.get("first_name"),
        "middle_name": user.get("middle_name"),
        "last_name": user.get("last_name"),
        "email": user.get("email")
    }

@router.post("/unlock/{user_id}")
@tracker.measure_async_time
async def unlock_user(user_id: str, current_user: Any = Depends(require_admin)) -> Dict[str, Any]:
    """
    🔓 Unlock user account (Admin only)
    
    This will reset the login attempts counter for the specified user.
    """
    success = await auth_service.unlock_user(user_id)
    if not success:
        return {"status": "error", "message": "Failed to unlock user"}
    return {"status": "success", "message": "User unlocked successfully"}

@router.get("/encrypt-password/{password}", response_model=str)
@tracker.measure_async_time
async def encrypt_password(password: str) -> str:
    """
    🔐 Encrypt password
    """
    return auth_service.get_password_hash(password)


@router.post("/refresh", response_model=Token)
@tracker.measure_async_time
async def refresh_token(request: Request, refresh_request: RefreshTokenRequest) -> Token:
    """
    🔄 Refresh access token using a refresh token
    """
    # Get client information
    ip_address = request.client.host if request.client else "unknown"
    
    # Refresh the token
    new_token = await auth_service.refresh_access_token(refresh_request.refresh_token)
    if not new_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
    
    return new_token


@router.post("/logout")
@tracker.measure_async_time
async def logout(refresh_request: RefreshTokenRequest) -> Dict[str, Any]:
    """
    🚪 Logout - revoke the refresh token
    """
    # Revoke the refresh token
    success = auth_service.revoke_refresh_token(refresh_request.refresh_token)
    
    return {"status": "success" if success else "error", 
            "message": "Successfully logged out" if success else "Invalid token"}

@router.patch("/change-password/{user_id}")
@tracker.measure_async_time
async def change_password(user_id: str, password_request: ChangePasswordRequest, current_user: Any = Depends(require_user)) -> Dict[str, Any]:
    """
    🔐 เปลี่ยนรหัสผ่าน (Admin สามารถเปลี่ยนของทุกคนได้, User สามารถเปลี่ยนของตัวเองได้)
    """
    if not current_user.user_id:
        raise HTTPException(status_code=400, detail="Insufficient permissions")
    # Check permissions: Admin can change anyone's password, users can only change their own
    if current_user.user_id != user_id and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return await user_service.change_password(user_id, password_request, current_user.user_id)
