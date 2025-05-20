from typing import Optional, Dict, List
from bson import ObjectId
from app.database import get_collection
from app.utils.serializers import list_serial, individual_serial

class FileRepository:
    async def save_file_metadata(self, file_data: Dict) -> str:
        """Save file metadata to database"""
        files_collection = await get_collection("files")
        result = await files_collection.insert_one(file_data)
        return str(result.inserted_id)

    async def get_file_by_id(self, file_id: str) -> Optional[Dict]:
        """Get file by ID"""
        if not ObjectId.is_valid(file_id):
            return None

        files_collection = await get_collection("files")
        file = await files_collection.find_one({"_id": ObjectId(file_id)})
        if file:
            return individual_serial(file)
        return None

    async def get_all_files(self, page: int = 1, limit: int = 10) -> Dict:
        """Get all files with pagination"""
        files_collection = await get_collection("files")
        
        skip = (page - 1) * limit
        total = await files_collection.count_documents({})
        
        cursor = files_collection.find().sort("upload_date", -1).skip(skip).limit(limit)
        files = await cursor.to_list(length=limit)
        
        return {
            "files": list_serial(files),
            "total": total,
            "page": page,
            "limit": limit
        }
