"""
User Repository

จัดการการเข้าถึงข้อมูลผู้ใช้ในฐานข้อมูล
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from app.repositories.base_repository import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository):
    """
    Repository สำหรับการเข้าถึงข้อมูลผู้ใช้
    """
    def __init__(self):
        super().__init__("users")
    
    async def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหาผู้ใช้ด้วย username
        """
        collection = await self._get_collection()
        user = await collection.find_one({"username": username})
        return user
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหาผู้ใช้ด้วย email
        """
        collection = await self._get_collection()
        user = await collection.find_one({"email": email})
        return user
    
    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหาผู้ใช้ด้วย ID
        """
        collection = await self._get_collection()
        if not ObjectId.is_valid(user_id):
            return None
        
        user = await collection.find_one({"_id": ObjectId(user_id)})
        return user
    
    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        สร้างผู้ใช้ใหม่
        """
        collection = await self._get_collection()
        
        # เพิ่ม timestamp
        current_time = datetime.now()
        user_data["created_at"] = current_time
        user_data["updated_at"] = current_time
        
        result = await collection.insert_one(user_data)
        created_user = await collection.find_one({"_id": result.inserted_id})
        
        return created_user
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        อัปเดตข้อมูลผู้ใช้
        """
        collection = await self._get_collection()
        
        # เพิ่ม timestamp
        update_data["updated_at"] = datetime.now()
        
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            # ไม่มีการเปลี่ยนแปลงข้อมูล หรือไม่พบผู้ใช้
            return None
        
        updated_user = await collection.find_one({"_id": ObjectId(user_id)})
        return updated_user
    
    async def delete(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ลบผู้ใช้
        """
        collection = await self._get_collection()
        
        # หาข้อมูลผู้ใช้ก่อนลบ
        user = await collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return None
        
        result = await collection.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            return None
        
        return user
    
    async def find_all(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ดึงรายการผู้ใช้ทั้งหมด
        """
        collection = await self._get_collection()
        cursor = collection.find().skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        return users
    
    async def count(self) -> int:
        """
        นับจำนวนผู้ใช้ทั้งหมด
        """
        collection = await self._get_collection()
        count = await collection.count_documents({})
        
        return count