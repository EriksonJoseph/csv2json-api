"""
Task Repository

จัดการการเข้าถึงข้อมูลงานในฐานข้อมูล
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from app.repositories.base_repository import BaseRepository

class TaskRepository(BaseRepository):
    """
    Repository สำหรับการเข้าถึงข้อมูลงาน
    """
    def __init__(self):
        super().__init__("tasks")
    
    async def find_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหางานด้วย ID
        """
        collection = await self._get_collection()
        if not ObjectId.is_valid(task_id):
            return None
        
        task = await collection.find_one({"_id": ObjectId(task_id)})
        return task
    
    async def create(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        สร้างงานใหม่
        """
        collection = await self._get_collection()
        
        # เพิ่ม timestamp
        current_time = datetime.now()
        task_data["created_at"] = current_time
        task_data["updated_at"] = current_time
        
        result = await collection.insert_one(task_data)
        created_task = await collection.find_one({"_id": result.inserted_id})
        
        return created_task
    
    async def update(self, task_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        อัปเดตข้อมูลงาน
        """
        collection = await self._get_collection()
        
        # เพิ่ม timestamp
        update_data["updated_at"] = datetime.now()
        
        result = await collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0 and len(update_data) > 1:  # มีมากกว่า updated_at
            # ไม่มีการเปลี่ยนแปลงข้อมูล หรือไม่พบงาน
            return None
        
        updated_task = await collection.find_one({"_id": ObjectId(task_id)})
        return updated_task
    
    async def delete(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        ลบงาน
        """
        collection = await self._get_collection()
        
        # หาข้อมูลงานก่อนลบ
        task = await collection.find_one({"_id": ObjectId(task_id)})
        
        if not task:
            return None
        
        result = await collection.delete_one({"_id": ObjectId(task_id)})
        
        if result.deleted_count == 0:
            return None
        
        return task
    
    async def find_all(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ดึงรายการงานทั้งหมด
        """
        collection = await self._get_collection()
        cursor = collection.find().sort("created_at", -1).skip(skip).limit(limit)
        tasks = await cursor.to_list(length=limit)
        
        return tasks
    
    async def count(self) -> int:
        """
        นับจำนวนงานทั้งหมด
        """
        collection = await self._get_collection()
        count = await collection.count_documents({})
        
        return count