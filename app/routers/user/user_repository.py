from typing import Optional, Dict, List, Any
from datetime import datetime
from bson import ObjectId # type: ignore
from app.database import get_collection
from app.utils.serializers import list_serial, individual_serial

class UserRepository:
    async def create(self, user_data: Dict[str, Any], created_by: str = "system") -> Dict[str, Any]:
        """Create a new user in the database"""
        users_collection = await get_collection("users")
        
        # Add audit fields
        user_data.update({
            "created_by": created_by,
            "created_at": datetime.now(),
            "updated_by": created_by,
            "updated_at": datetime.now()
        })
        
        result = await users_collection.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        return user_data

    async def find_by_id(self, user_id: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if not ObjectId.is_valid(user_id):
            return None

        users_collection = await get_collection("users")
        projection = None if include_password else {"password": 0}
        user = await users_collection.find_one({"_id": ObjectId(user_id)}, projection)
        if user:
            if include_password:
                # Convert ObjectId to string manually when including password
                user["_id"] = str(user["_id"])
                return user
            else:
                return individual_serial(user)
        return None

    async def find_by_username(self, username: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        users_collection = await get_collection("users")
        projection = None if include_password else {"password": 0}
        user = await users_collection.find_one({"username": username}, projection)
        if user:
            # Convert ObjectId to string
            user["_id"] = str(user["_id"])
            return user
        return None

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        users_collection = await get_collection("users")
        user = await users_collection.find_one({"email": email}, {"password": 0})
        if user:
            return individual_serial(user)
        return None

    async def update_user(self, user_id: str, update_data: Dict[str, Any], updated_by: str) -> Optional[str]:
        """Update user information
        
        Args:
            user_id: The ID of the user to update
            update_data: A dictionary containing the update operations.
                       Must be a MongoDB update operation (e.g., {'$set': {...}}, {'$push': {...}})
            updated_by: User ID of who is making the update
        """
        if not ObjectId.is_valid(user_id):
            return None

        users_collection = await get_collection("users")
        
        # Ensure the update operation is valid
        if not any(key.startswith('$') for key in update_data.keys()):
            # If no operators found, wrap in $set
            update_fields = update_data
        else:
            # Extract fields from $set operation if it exists
            update_fields = update_data.get('$set', {})
        
        # Add audit fields
        update_fields.update({
            "updated_by": updated_by,
            "updated_at": datetime.now()
        })
        
        update_operation = {"$set": update_fields}
            
        try:
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                update_operation
            )
            
            if result.matched_count == 0:
                return None
                
            updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if updated_user:
                return "Update user successfully"
            return None
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error updating user {user_id}: {str(e)}")
            raise

    async def get_all_users(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get all users with pagination"""
        users_collection = await get_collection("users")
        
        skip = (page - 1) * limit
        total = await users_collection.count_documents({})
        
        cursor = users_collection.find({}, {"password": 0}).sort("created_at", -1).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        return {
            "list": list_serial(users),
            "total": total,
            "page": page,
            "limit": limit
        }
    
    async def find_by_verification_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Find user by email verification token"""
        users_collection = await get_collection("users")
        user = await users_collection.find_one({"email_verification_token": token})
        return individual_serial(user) if user else None
