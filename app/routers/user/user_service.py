from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId # type: ignore
from app.routers.user.user_repository import UserRepository
from app.routers.user.user_model import UserCreate, UserUpdate, ChangePasswordRequest
from app.exceptions import UserException
from app.routers.auth.auth_model import TokenData

class UserService:
    def __init__(self) -> None:
        self.user_repository: UserRepository = UserRepository()

    async def create_user(self, user: UserCreate, user_id: str) -> Dict[str, Any]:
        """Create a new user"""
        # Check for duplicate username
        if await self.user_repository.find_by_username(user.username):
            raise UserException("Username already exists", status_code=400)
        
        # Check for duplicate email
        if await self.user_repository.find_by_email(user.email):
            raise UserException("Email already exists", status_code=400)

        # Prepare user data
        user_data = {
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "roles": user.roles if hasattr(user, 'roles') else ["user"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Create user
        return await self.user_repository.create(user_data, user_id)

    async def update_user(self, user_id: str, user_update: UserUpdate, acting_user_id: str) -> Optional[Dict[str, Any]]:
        """Update user information"""
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        # Get existing user
        existing_user = await self.user_repository.find_by_id(user_id)
        if not existing_user:
            raise UserException("User not found", status_code=404)

        # Prepare update data
        update_data = user_update.dict(exclude_unset=False)
        update_data["updated_at"] = datetime.utcnow()

        # Check for username update and validate uniqueness
        if "username" in update_data:
            if update_data["username"] != existing_user["username"]:
                existing_username = await self.user_repository.find_by_username(update_data["username"])
                if existing_username and str(existing_username["_id"]) != user_id:
                    raise UserException("Username already exists", status_code=400)

        # Update user
        result = await self.user_repository.update_user(user_id, {"$set": update_data}, acting_user_id)
        if not result:
            return None
        
        # Return the updated user data
        return await self.user_repository.find_by_id(user_id)

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserException("User not found", status_code=404)
        return user

    async def get_all_users(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get all users with pagination"""
        return await self.user_repository.get_all_users(page, limit)

    async def change_password(self, user_id: str, password_request: ChangePasswordRequest, acting_user_id: str) -> Dict[str, Any]:
        """Change user password"""
        from app.routers.auth.auth_service import AuthService
        auth_service = AuthService()
        
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        # Get existing user with password
        existing_user = await self.user_repository.find_by_id(user_id, include_password=True)
        if not existing_user:
            raise UserException("User not found", status_code=404)

        # Verify new password and confirm password match
        if password_request.new_password != password_request.confirm_password:
            raise UserException("New password and confirm password do not match", status_code=400)

        # Verify old password
        if not auth_service.verify_password(password_request.old_password, existing_user["password"]):
            raise UserException("Current password is incorrect", status_code=400)

        # Hash new password
        new_password_hash = auth_service.get_password_hash(password_request.new_password)

        # Update password
        update_data = {
            "password": new_password_hash,
            "updated_at": datetime.utcnow()
        }

        result = await self.user_repository.update_user(user_id, {"$set": update_data}, acting_user_id)
        if not result:
            raise UserException("Failed to update password", status_code=500)

        return {"message": "Password changed successfully"}
