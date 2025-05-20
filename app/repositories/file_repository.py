"""
File Repository

จัดการการเข้าถึงข้อมูลไฟล์ในฐานข้อมูล
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from app.repositories.base_repository import BaseRepository

class FileRepository(BaseRepository):
    """
    Repository สำหรับการเข้าถึงข้อมูลไฟล์
    """
    def __init__(self):
        super().__init__("files")
    
    async def find_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหาไฟล์ด้วย ID
        """
        collection = await self._get_collection()
        if not ObjectId.is_valid(file_id):
            return None
        
        file = await collection.find_one({"_id": ObjectId(file_id)})
        return file
    
    async def find_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหาไฟล์ด้วยชื่อไฟล์
        """
        collection = await self._get_collection()
        file = await collection.find_one({"filename": filename})
        return file
    
    async def create(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        บันทึกข้อมูลไฟล์ใหม่
        """
        collection = await self._get_collection()
        
        # ตรวจสอบว่ามีการกำหนด _id หรือไม่
        if "_id" not in file_data:
            file_data["_id"] = ObjectId()
        
        result = await collection.insert_one(file_data)
        created_file = await collection.find_one({"_id": result.inserted_id})
        
        return created_file
    
    async def update(self, file_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        อัปเดตข้อมูลไฟล์
        """
        collection = await self._get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(file_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            # ไม่มีการเปลี่ยนแปลงข้อมูล หรือไม่พบไฟล์
            return None
        
        updated_file = await collection.find_one({"_id": ObjectId(file_id)})
        return updated_file
    
    async def delete(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        ลบข้อมูลไฟล์
        """
        collection = await self._get_collection()
        
        # หาข้อมูลไฟล์ก่อนลบ
        file = await collection.find_one({"_id": ObjectId(file_id)})
        
        if not file:
            return None
        
        result = await collection.delete_one({"_id": ObjectId(file_id)})
        
        if result.deleted_count == 0:
            return None
        
        return file
    
    async def find_all(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ดึงรายการไฟล์ทั้งหมด
        """
        collection = await self._get_collection()
        cursor = collection.find().sort("upload_date", -1).skip(skip).limit(limit)
        files = await cursor.to_list(length=limit)
        
        return files
    
    async def count(self) -> int:
        """
        นับจำนวนไฟล์ทั้งหมด
        """
        collection = await self._get_collection()
        count = await collection.count_documents({})
        
        return count