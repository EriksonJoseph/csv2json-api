from typing import Optional
from bson import ObjectId
from app.database import get_collection

class FileRepository:
    async def get_file_by_id(self, file_id: str) -> Optional[dict]:
        """Get file by ID"""
        files_collection = await get_collection("files")
        
        if not ObjectId.is_valid(file_id):
            return None
            
        return await files_collection.find_one({"_id": ObjectId(file_id)})
