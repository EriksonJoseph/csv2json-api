import os
import shutil
from datetime import datetime
from app.database import get_collection
from bson import ObjectId
from fastapi import UploadFile
from app.utils.advanced_performance import tracker, TimedBlock

@tracker.measure_async_time
async def save_file_to_temp(file: UploadFile) -> dict:
    """
    บันทึกไฟล์ที่อัปโหลดไว้ที่โฟลเดอร์ temp และบันทึกข้อมูลไฟล์ลงใน collection files
    
    Args:
        file: ไฟล์ที่อัปโหลด
    
    Returns:
        ข้อมูลไฟล์ที่บันทึกแล้ว
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
            "_id": ObjectId(),
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
        files_collection = await get_collection("files")
        await files_collection.insert_one(file_data)
        
        # แปลง ObjectId เป็น string เพื่อส่งกลับ
        file_data["_id"] = str(file_data["_id"])
        
        return file_data