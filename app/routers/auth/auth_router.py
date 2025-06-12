from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Dict, Any
from app.routers.auth.auth_model import UserLogin, Token, RefreshTokenRequest
from app.routers.user.user_model import UserCreate
from app.dependencies.auth import get_current_user, require_admin
from app.utils.advanced_performance import tracker
from app.routers.auth.auth_service import AuthService

# Create a router instance
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Create instance of AuthService
auth_service = AuthService()

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
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "roles": current_user.roles
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
