"""
CSV Repository

จัดการการเข้าถึงข้อมูล CSV ในฐานข้อมูล
"""
from typing import Dict, List, Any
from app.repositories.base_repository import BaseRepository

class CSVRepository(BaseRepository):
    """
    Repository สำหรับการเข้าถึงข้อมูล CSV
    """
    def __init__(self):
        super().__init__("csv")
    
    async def insert_many(self, csv_data: List[Dict[str, Any]]) -> int:
        """
        บันทึกข้อมูล CSV จำนวนมาก
        
        Returns:
            จำนวนเอกสารที่ถูกเพิ่ม
        """
        collection = await self._get_collection()
        
        if not csv_data:
            return 0
        
        result = await collection.insert_many(csv_data)
        return len(result.inserted_ids)
    
    async def delete_all(self) -> int:
        """
        ลบข้อมูล CSV ทั้งหมด
        
        Returns:
            จำนวนเอกสารที่ถูกลบ
        """
        collection = await self._get_collection()
        
        # นับจำนวนเอกสารก่อนลบ
        count = await collection.count_documents({})
        
        # ลบข้อมูลทั้งหมด
        await collection.delete_many({})
        
        return count
    
    async def count(self) -> int:
        """
        นับจำนวนเอกสาร CSV ทั้งหมด
        """
        collection = await self._get_collection()
        count = await collection.count_documents({})
        
        return count