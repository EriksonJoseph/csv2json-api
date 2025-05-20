# app/repositories/base_repository.py
"""
Base Repository

เป็นคลาสพื้นฐานสำหรับ repository ทั้งหมด
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from app.config import get_settings

settings = get_settings()

class BaseRepository:
    """
    คลาสพื้นฐานสำหรับการเข้าถึงข้อมูลในฐานข้อมูล
    """
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._client: AsyncIOMotorClient = None
        self._db: AsyncIOMotorDatabase = None
        self._collection: AsyncIOMotorCollection = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """
        เชื่อมต่อกับ collection ใน MongoDB
        """
        if self._collection is None:
            self._client = AsyncIOMotorClient(settings.MONGODB_URI)
            self._db = self._client[settings.MONGODB_DB]
            self._collection = self._db[self.collection_name]
        
        return self._collection