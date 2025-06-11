from typing import Optional, Dict, List
from bson import ObjectId
from datetime import datetime
from app.database import get_collection
from app.utils.serializers import list_serial, individual_serial
from app.routers.file.file_model import UploadStatus

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
            "list": list_serial(files),
            "total": total,
            "page": page,
            "limit": limit
        }

    async def delete_file_by_id(self, file_id: str) -> None:
        """Delete file by ID from database"""
        if not ObjectId.is_valid(file_id):
            raise ValueError("Invalid file_id format")

        files_collection = await get_collection("files")
        await files_collection.delete_one({"_id": ObjectId(file_id)})

    async def create_chunked_upload(self, upload_data: Dict) -> str:
        """Create new chunked upload session"""
        uploads_collection = await get_collection("chunked_uploads")
        result = await uploads_collection.insert_one(upload_data)
        return str(result.inserted_id)

    async def get_chunked_upload(self, upload_id: str) -> Optional[Dict]:
        """Get chunked upload session by ID"""
        if not ObjectId.is_valid(upload_id):
            return None

        uploads_collection = await get_collection("chunked_uploads")
        upload = await uploads_collection.find_one({"_id": ObjectId(upload_id)})
        if upload:
            return individual_serial(upload)
        return None

    async def update_chunked_upload(self, upload_id: str, update_data: Dict) -> bool:
        """Update chunked upload session"""
        if not ObjectId.is_valid(upload_id):
            return False

        uploads_collection = await get_collection("chunked_uploads")
        result = await uploads_collection.update_one(
            {"_id": ObjectId(upload_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_chunked_upload(self, upload_id: str) -> None:
        """Delete chunked upload session"""
        if not ObjectId.is_valid(upload_id):
            raise ValueError("Invalid upload_id format")

        uploads_collection = await get_collection("chunked_uploads")
        await uploads_collection.delete_one({"_id": ObjectId(upload_id)})

    async def add_received_chunk(self, upload_id: str, chunk_number: int) -> bool:
        """Add chunk number to received chunks list"""
        if not ObjectId.is_valid(upload_id):
            return False

        uploads_collection = await get_collection("chunked_uploads")
        result = await uploads_collection.update_one(
            {"_id": ObjectId(upload_id)},
            {
                "$addToSet": {"received_chunks": chunk_number},
                "$set": {"updated_at": datetime.now()}
            }
        )
        return result.modified_count > 0
