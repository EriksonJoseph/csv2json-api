from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.login_repository import LoginRepository
from app.models.auth import TokenData, UserRole
from app.exceptions import UserException
from app.utils.advanced_performance import tracker

# Initialize services
user_repository = UserRepository()
login_repository = LoginRepository()
auth_service = AuthService(user_repository, login_repository)

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
    user = await user_repository.get_user_by_id(current_user.user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    return current_user

def require_roles(required_roles: List[UserRole]):
    def role_checker(current_user: TokenData = Depends(get_current_active_user)) -> TokenData:
        user_roles = [UserRole(role) for role in current_user.roles]
        
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
