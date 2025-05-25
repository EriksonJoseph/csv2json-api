from typing import Optional, Dict
from datetime import datetime
from bson import ObjectId
from app.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserUpdate
from app.exceptions import UserException
from app.services.base_service import BaseService
from app.models.auth import TokenData

class UserService(BaseService):
    def __init__(self, user_repository: UserRepository):
        super().__init__(user_repository)
        self.user_repository = user_repository

    async def create_user(self, user: UserCreate, current_user: Optional[TokenData] = None) -> Dict:
        """Create a new user"""
        # Check for duplicate username
        if await self.user_repository.get_user_by_username(user.username):
            raise UserException("Username already exists", status_code=400)
        
        # Check for duplicate email
        if await self.user_repository.get_user_by_email(user.email):
            raise UserException("Email already exists", status_code=400)

        # Prepare user data
        user_data = {
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "roles": user.roles if hasattr(user, 'roles') else ["user"]  # ใช้ roles ที่มีหรือ default เป็น ["user"]
        }

        # Create user with audit fields
        return await self.create(user_data, current_user)

    async def update_user(self, user_id: str, user_update: UserUpdate, current_user: Optional[TokenData] = None) -> Dict:
        """Update user information"""
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        # Get existing user
        existing_user = await self.user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise UserException("User not found", status_code=404)

        # Prepare update data
        update_data = user_update.dict(exclude_unset=True)

        # Check for username update and validate uniqueness
        if "username" in update_data:
            if update_data["username"] != existing_user["username"]:
                existing_username = await self.user_repository.get_user_by_username(update_data["username"])
                if existing_username and str(existing_username["_id"]) != user_id:
                    raise UserException("Username already exists", status_code=400)

        # Update user with audit fields
        return await self.update(user_id, update_data, current_user)
        # Update user
        updated_user = await self.user_repository.update_user(user_id, update_data)
        return updated_user

    async def get_user(self, user_id: str) -> Dict:
        """Get user by ID"""
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserException("User not found", status_code=404)
        return user

    async def get_all_users(self, page: int = 1, limit: int = 10) -> Dict:
        """Get all users with pagination"""
        return await self.user_repository.get_all_users(page, limit)
