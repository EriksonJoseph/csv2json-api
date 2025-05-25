from typing import Optional, Dict, List
from datetime import datetime
from bson import ObjectId
from app.database import get_collection
from app.utils.serializers import list_serial, individual_serial

class UserRepository:
    async def create(self, user_data: Dict) -> Dict:
        """Create a new user in the database"""
        users_collection = await get_collection("users")
        result = await users_collection.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        return user_data

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        if not ObjectId.is_valid(user_id):
            return None

        users_collection = await get_collection("users")
        user = await users_collection.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        if user:
            return individual_serial(user)
        return None

    async def get_user_by_username(self, username: str, include_password: bool = False) -> Optional[Dict]:
        """Get user by username"""
        users_collection = await get_collection("users")
        projection = None if include_password else {"password": 0}
        user = await users_collection.find_one({"username": username}, projection)
        if user:
            # Convert ObjectId to string
            user["_id"] = str(user["_id"])
            return user
        return None

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        users_collection = await get_collection("users")
        user = await users_collection.find_one({"email": email}, {"password": 0})
        if user:
            return individual_serial(user)
        return None

    async def update_user(self, user_id: str, update_data: Dict) -> Dict:
        """Update user information
        
        Args:
            user_id: The ID of the user to update
            update_data: A dictionary containing the update operations.
                       Must be a MongoDB update operation (e.g., {'$set': {...}}, {'$push': {...}})
        """
        if not ObjectId.is_valid(user_id):
            return None

        users_collection = await get_collection("users")
        
        # Ensure the update operation is valid
        if not any(key.startswith('$') for key in update_data.keys()):
            # If no operators found, wrap in $set
            update_operation = {"$set": update_data}
        else:
            update_operation = update_data
            
        try:
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                update_operation
            )
            
            if result.matched_count == 0:
                return None
                
            updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if updated_user:
                return individual_serial(updated_user)
            return None
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error updating user {user_id}: {str(e)}")
            raise

    async def get_all_users(self, page: int = 1, limit: int = 10) -> Dict:
        """Get all users with pagination"""
        users_collection = await get_collection("users")
        
        skip = (page - 1) * limit
        total = await users_collection.count_documents({})
        
        cursor = users_collection.find({}, {"password": 0}).sort("created_at", -1).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        return {
            "users": list_serial(users),
            "total": total,
            "page": page,
            "limit": limit
        }
