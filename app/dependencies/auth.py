from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Callable
from app.routers.auth.auth_service import AuthService
from app.routers.auth.auth_model import TokenData, UserRole
from app.exceptions import UserException
from app.utils.advanced_performance import tracker

# Initialize services
auth_service = AuthService()

# Security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    token = credentials.credentials
    user_data = await auth_service.verify_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_data

async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    from app.routers.user.user_repository import UserRepository
    user_repository = UserRepository()
    user = await user_repository.find_by_id(current_user.user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    return current_user

def require_roles(required_roles: List[UserRole]) -> Callable[[TokenData], TokenData]:
    def role_checker(current_user: TokenData = Depends(get_current_active_user)) -> TokenData:
        # Map inconsistent role names to correct enum values
        role_mapping = {"users": "user"}
        user_roles = []
        for role in current_user.roles:
            mapped_role = role_mapping.get(role, role)
            user_roles.append(UserRole(mapped_role))
        
        # Admin has all permissions
        if UserRole.ADMIN in user_roles:
            return current_user
            
        # Check if user has any required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Shortcut dependencies for different roles
require_admin = require_roles([UserRole.ADMIN])
require_moderator = require_roles([UserRole.ADMIN, UserRole.MODERATOR])
require_user = require_roles([UserRole.ADMIN, UserRole.MODERATOR, UserRole.USER])
