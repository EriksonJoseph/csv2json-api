"""
File Service

ดำเนินการเกี่ยวกับไฟล์
"""
import os
import shutil
from datetime import datetime
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from app.repositories.file_repository import FileRepository
from app.api.schemas.file_schemas import FileResponse
from app.api.schemas.response_schemas import ResponseModel, PaginatedResponse
from app.utils.advanced_performance import tracker, TimedBlock
from bson import ObjectId
from typing import Dict, Any, List

class FileService:
    """
    Service สำหรับจัดการไฟล์
    """
    def __init__(self, repository: FileRepository):
        self.repository = repository
    
    @tracker.measure_async_time
    async def save_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        บันทึกไฟล์ที่อัปโหลดไว้ที่โฟลเดอร์ temp และบันทึกข้อมูลไฟล์ลงใน collection files
        """
        # สร้างโฟลเดอร์ temp ถ้ายังไม่มี
        temp_folder = "temp"
        os.makedirs(temp_folder, exist_ok=True)
        
        with TimedBlock("Save File Operation"):
            # สร้าง filename ใหม่ด้วย timestamp และ original filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_extension = os.path.splitext(file.filename)[1] # type: ignore
            new_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(temp_folder, new_filename)
            
            # บันทึกไฟล์
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # หาขนาดไฟล์
            file_size = os.path.getsize(file_path)
            
            # เตรียมข้อมูลสำหรับบันทึกลง MongoDB
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
            
            # บันทึกข้อมูลลง MongoDB
            created_file = await self.repository.create(file_data)
            
            # แปลง ObjectId เป็น string เพื่อส่งกลับ
            file_dict = {**created_file}
            file_dict["id"] = str(file_dict.pop("_id"))
            
            return file_dict
    
    @tracker.measure_async_time
    async def get_all_files(self, page: int, limit: int) -> PaginatedResponse:
        """
        ดึงรายการไฟล์ทั้งหมด
        """
        # คำนวณ skip สำหรับ pagination
        skip = (page - 1) * limit
        
        # นับจำนวนไฟล์ทั้งหมด
        total_files = await self.repository.count()
        
        # ดึงข้อมูลโดยมีการทำ pagination
        files_list = await self.repository.find_all(skip, limit)
        
        # แปลง ObjectId เป็น string และ datetime เป็น string
        files = []
        for file in files_list:
            file_dict = {**file}
            file_dict["id"] = str(file_dict.pop("_id"))
            if isinstance(file_dict["upload_date"], datetime):
                file_dict["upload_date"] = file_dict["upload_date"].isoformat()
            files.append(file_dict)
        
        return PaginatedResponse(
            message="📁 รายการไฟล์ทั้งหมด",
            total=total_files,
            page=page,
            limit=limit,
            pages=(total_files + limit - 1) // limit,
            data=files
        )
    
    @tracker.measure_async_time
    async def download_file(self, file_id: str) -> FileResponse:
        """
        ดาวน์โหลดไฟล์ตาม ID
        """
        # ดึงข้อมูลไฟล์
        file_data = await self.repository.find_by_id(file_id)
        
        # ตรวจสอบว่าพบไฟล์หรือไม่
        if not file_data:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบไฟล์ที่ต้องการ")
        
        # ตรวจสอบว่าไฟล์ยังมีอยู่ในระบบหรือไม่
        file_path = file_data["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="🔍 ไฟล์ไม่มีอยู่ในระบบแล้ว")
        
        # ส่งไฟล์กลับเพื่อดาวน์โหลด
        return FileResponse(
            path=file_path,
            filename=file_data["original_filename"],
            media_type=file_data["mime_type"]
        )