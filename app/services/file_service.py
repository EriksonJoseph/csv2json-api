import os
import shutil
from datetime import datetime
from bson import ObjectId
from fastapi import UploadFile
from fastapi.responses import FileResponse
from app.repositories.file_repository import FileRepository
from app.exceptions import FileException

class FileService:
    def __init__(self, file_repository: FileRepository):
        self.file_repository = file_repository

    async def upload_file(self, file: UploadFile) -> dict:
        """
        Upload file to temporary storage and save metadata
        
        Args:
            file: File to upload
        
        Returns:
            File metadata
        
        Raises:
            FileException: If file upload fails
        """
        if not file.filename:
            raise FileException("No file provided", status_code=400)

        try:
            # Create temp folder if it doesn't exist
            temp_folder = "temp"
            os.makedirs(temp_folder, exist_ok=True)
            
            # Create new filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_extension = os.path.splitext(file.filename)[1]
            new_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(temp_folder, new_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Prepare file metadata
            file_data = {
                "filename": new_filename,
                "original_filename": file.filename,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": file.content_type,
                "file_extension": file_extension,
                "upload_date": datetime.now(),
                "metadata": {}
            }
            
            # Save metadata to database
            file_id = await self.file_repository.save_file_metadata(file_data)
            file_data["_id"] = file_id
            
            return file_data
            
        except Exception as e:
            raise FileException(f"Failed to upload file: {str(e)}", status_code=500)

    async def get_all_files(self, page: int = 1, limit: int = 10) -> dict:
        """
        Get all files with pagination
        
        Args:
            page: Page number (default: 1)
            limit: Number of items per page (default: 10)
        
        Returns:
            Dictionary containing files list and pagination info
        """
        try:
            return await self.file_repository.get_all_files(page, limit)
        except Exception as e:
            raise FileException(f"Failed to retrieve files: {str(e)}", status_code=500)

    async def download_file(self, file_id: str) -> FileResponse:
        """
        Download file by ID
        
        Args:
            file_id: ID of the file to download
        
        Returns:
            FileResponse with the file content
        
        Raises:
            FileException: If file not found or download fails
        """
        try:
            # Get file metadata from repository
            file_data = await self.file_repository.get_file_by_id(file_id)
            if not file_data:
                raise FileException("File not found", status_code=404)

            # Check if file exists on disk
            if not os.path.exists(file_data["file_path"]):
                raise FileException("File not found on disk", status_code=404)

            # Create FileResponse with proper headers for browser download
            return FileResponse(
                file_data["file_path"],
                filename=file_data["original_filename"],
                media_type=file_data["mime_type"],
                headers={
                    "Content-Disposition": f"attachment; filename={file_data['original_filename']}"
                }
            )
        except Exception as e:
            raise FileException(f"Failed to download file: {str(e)}", status_code=500)

    async def get_file_by_id(self, file_id: str) -> dict:
        """
        Get file metadata by ID
        
        Args:
            file_id: ID of the file
        
        Returns:
            File metadata
        
        Raises:
            FileException: If file not found
        """
        try:
            file_data = await self.file_repository.get_file_by_id(file_id)
            if not file_data:
                raise FileException("File not found", status_code=404)
            return file_data
        except Exception as e:
            raise FileException(f"Failed to get file: {str(e)}", status_code=500)

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file from server and database
        
        Args:
            file_id: ID of the file to delete
        
        Returns:
            True if deletion was successful
        
        Raises:
            FileException: If deletion fails
        """
        try:
            # Get file metadata
            file_data = await self.file_repository.get_file_by_id(file_id)
            if not file_data:
                raise FileException("File not found", status_code=404)

            # Delete file from disk
            if os.path.exists(file_data["file_path"]):
                os.remove(file_data["file_path"])

            # Delete file from database
            await self.file_repository.delete_file_by_id(file_id)
            return True
        except Exception as e:
            raise FileException(f"Failed to delete file: {str(e)}", status_code=500)