import os
import shutil
import uuid
from datetime import datetime
from fastapi import UploadFile
from fastapi.responses import FileResponse
from app.routers.file.file_repository import FileRepository
from app.routers.file.file_model import UploadStatus, InitiateUploadRequest
from app.exceptions import FileException

class FileService:
    def __init__(self):
        self.file_repository = FileRepository()

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

    async def initiate_chunked_upload(self, request: InitiateUploadRequest) -> dict:
        """
        Initiate chunked upload session
        
        Args:
            request: Upload initialization data
        
        Returns:
            Upload session information
        """
        try:
            total_chunks = (request.total_size + request.chunk_size - 1) // request.chunk_size
            
            upload_data = {
                "original_filename": request.filename,
                "total_chunks": total_chunks,
                "chunk_size": request.chunk_size,
                "total_size": request.total_size,
                "mime_type": request.mime_type,
                "status": UploadStatus.PENDING,
                "received_chunks": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            upload_id = await self.file_repository.create_chunked_upload(upload_data)
            
            # Create temp directory for chunks
            chunks_dir = os.path.join("temp", "chunks", upload_id)
            os.makedirs(chunks_dir, exist_ok=True)
            
            return {
                "upload_id": upload_id,
                "total_chunks": total_chunks,
                "chunk_size": request.chunk_size,
                "status": UploadStatus.PENDING
            }
            
        except Exception as e:
            raise FileException(f"Failed to initiate chunked upload: {str(e)}", status_code=500)

    async def upload_chunk(self, upload_id: str, chunk_number: int, chunk_data: UploadFile) -> dict:
        """
        Upload a single chunk
        
        Args:
            upload_id: Upload session ID
            chunk_number: Chunk number (0-based)
            chunk_data: Chunk file data
        
        Returns:
            Upload progress information
        """
        try:
            # Get upload session
            upload_session = await self.file_repository.get_chunked_upload(upload_id)
            if not upload_session:
                raise FileException("Upload session not found", status_code=404)
            
            if upload_session["status"] not in [UploadStatus.PENDING, UploadStatus.IN_PROGRESS]:
                raise FileException("Upload session is not active", status_code=400)
            
            # Validate chunk number
            if chunk_number >= upload_session["total_chunks"] or chunk_number < 0:
                raise FileException("Invalid chunk number", status_code=400)
            
            # Check if chunk already received
            if chunk_number in upload_session["received_chunks"]:
                raise FileException("Chunk already received", status_code=400)
            
            # Save chunk to temporary file
            chunks_dir = os.path.join("temp", "chunks", upload_id)
            chunk_path = os.path.join(chunks_dir, f"chunk_{chunk_number}")
            
            with open(chunk_path, "wb") as buffer:
                shutil.copyfileobj(chunk_data.file, buffer)
            
            # Update upload session
            await self.file_repository.add_received_chunk(upload_id, chunk_number)
            
            # Update status to in_progress if first chunk
            if upload_session["status"] == UploadStatus.PENDING:
                await self.file_repository.update_chunked_upload(
                    upload_id,
                    {"status": UploadStatus.IN_PROGRESS}
                )
            
            # Get updated session
            updated_session = await self.file_repository.get_chunked_upload(upload_id)
            if not updated_session:
                raise FileException("Upload session not found after update", status_code=404)
            received_count = len(updated_session["received_chunks"])
            
            # Check if all chunks received
            if received_count == upload_session["total_chunks"]:
                return await self._finalize_chunked_upload(upload_id)
            
            return {
                "upload_id": upload_id,
                "chunk_number": chunk_number,
                "received_chunks": received_count,
                "total_chunks": upload_session["total_chunks"],
                "status": UploadStatus.IN_PROGRESS,
                "progress": (received_count / upload_session["total_chunks"]) * 100
            }
            
        except Exception as e:
            raise FileException(f"Failed to upload chunk: {str(e)}", status_code=500)

    async def _finalize_chunked_upload(self, upload_id: str) -> dict:
        """
        Finalize chunked upload by combining all chunks
        
        Args:
            upload_id: Upload session ID
        
        Returns:
            Final file information
        """
        try:
            # Get upload session
            upload_session = await self.file_repository.get_chunked_upload(upload_id)
            if not upload_session:
                raise FileException("Upload session not found", status_code=404)
            
            # Create final filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_extension = os.path.splitext(upload_session["original_filename"])[1]
            final_filename = f"{timestamp}_{upload_session['original_filename']}"
            final_path = os.path.join("temp", final_filename)
            
            # Combine chunks
            chunks_dir = os.path.join("temp", "chunks", upload_id)
            with open(final_path, "wb") as final_file:
                for chunk_num in sorted(upload_session["received_chunks"]):
                    chunk_path = os.path.join(chunks_dir, f"chunk_{chunk_num}")
                    if os.path.exists(chunk_path):
                        with open(chunk_path, "rb") as chunk_file:
                            shutil.copyfileobj(chunk_file, final_file)
            
            # Verify file size
            final_size = os.path.getsize(final_path)
            if final_size != upload_session["total_size"]:
                raise FileException("File size mismatch after combining chunks", status_code=500)
            
            # Save file metadata
            file_data = {
                "filename": final_filename,
                "original_filename": upload_session["original_filename"],
                "file_path": final_path,
                "file_size": final_size,
                "mime_type": upload_session["mime_type"],
                "file_extension": file_extension,
                "upload_date": datetime.now(),
                "metadata": {"chunked_upload_id": upload_id}
            }
            
            file_id = await self.file_repository.save_file_metadata(file_data)
            file_data["_id"] = file_id
            
            # Update upload session status
            await self.file_repository.update_chunked_upload(
                upload_id,
                {"status": UploadStatus.COMPLETED, "file_id": file_id}
            )
            
            # Clean up chunk files
            if os.path.exists(chunks_dir):
                shutil.rmtree(chunks_dir)
            
            return {
                "upload_id": upload_id,
                "file_id": file_id,
                "status": UploadStatus.COMPLETED,
                "file_data": file_data
            }
            
        except Exception as e:
            # Mark upload as failed
            await self.file_repository.update_chunked_upload(
                upload_id,
                {"status": UploadStatus.FAILED}
            )
            raise FileException(f"Failed to finalize chunked upload: {str(e)}", status_code=500)

    async def get_chunked_upload_status(self, upload_id: str) -> dict:
        """
        Get chunked upload status
        
        Args:
            upload_id: Upload session ID
        
        Returns:
            Upload status information
        """
        try:
            upload_session = await self.file_repository.get_chunked_upload(upload_id)
            if not upload_session:
                raise FileException("Upload session not found", status_code=404)
            
            received_count = len(upload_session["received_chunks"])
            progress = (received_count / upload_session["total_chunks"]) * 100 if upload_session["total_chunks"] > 0 else 0
            
            return {
                "upload_id": upload_id,
                "status": upload_session["status"],
                "received_chunks": received_count,
                "total_chunks": upload_session["total_chunks"],
                "progress": progress,
                "created_at": upload_session["created_at"],
                "updated_at": upload_session["updated_at"]
            }
            
        except Exception as e:
            raise FileException(f"Failed to get upload status: {str(e)}", status_code=500)

    async def cancel_chunked_upload(self, upload_id: str) -> bool:
        """
        Cancel chunked upload
        
        Args:
            upload_id: Upload session ID
        
        Returns:
            True if cancellation was successful
        """
        try:
            upload_session = await self.file_repository.get_chunked_upload(upload_id)
            if not upload_session:
                raise FileException("Upload session not found", status_code=404)
            
            # Clean up chunk files
            chunks_dir = os.path.join("temp", "chunks", upload_id)
            if os.path.exists(chunks_dir):
                shutil.rmtree(chunks_dir)
            
            # Delete upload session
            await self.file_repository.delete_chunked_upload(upload_id)
            
            return True
            
        except Exception as e:
            raise FileException(f"Failed to cancel chunked upload: {str(e)}", status_code=500)
