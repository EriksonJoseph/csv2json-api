from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from app.services.file_service import save_file_to_temp
from app.database import get_collection
from app.utils.advanced_performance import tracker
from bson import ObjectId
import os

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not Found"}}
)

@router.post("/upload")
@tracker.measure_async_time
async def upload_file(file: UploadFile = File(...)):
    """
    🚀 อัปโหลดไฟล์และบันทึกลงโฟลเดอร์ temp พร้อมบันทึกข้อมูลลง collection files
    """
    try:
        # ตรวจสอบว่ามีไฟล์หรือไม่
        if not file.filename:
            raise HTTPException(status_code=400, detail="⚠️ ไม่พบไฟล์ที่อัปโหลด")
            
        # บันทึกไฟล์และข้อมูลไฟล์
        result = await save_file_to_temp(file)
        
        # ส่งคืนข้อมูลไฟล์ที่บันทึกแล้ว
        return {
            "message": "✅ อัปโหลดไฟล์สำเร็จ",
            "file": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ เกิดข้อผิดพลาดในการอัปโหลดไฟล์: {str(e)}")

@router.get("/")
@tracker.measure_async_time
async def get_all_files(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    📋 ดึงรายการไฟล์ทั้งหมด
    """
    # เชื่อมต่อกับ collection files
    files_collection = await get_collection("files")
    
    # คำนวณ skip สำหรับ pagination
    skip = (page - 1) * limit
    
    # นับจำนวนไฟล์ทั้งหมด
    total_files = await files_collection.count_documents({})
    
    # ดึงข้อมูลโดยมีการทำ pagination
    cursor = files_collection.find().sort("upload_date", -1).skip(skip).limit(limit)
    files_list = await cursor.to_list(length=limit)
    
    # แปลง ObjectId เป็น string
    for file in files_list:
        file["_id"] = str(file["_id"])
        file["upload_date"] = file["upload_date"].isoformat()
    
    # ส่งคืนข้อมูลพร้อม metadata สำหรับ pagination
    return {
        "message": "📁 รายการไฟล์ทั้งหมด",
        "total": total_files,
        "page": page,
        "limit": limit,
        "pages": (total_files + limit - 1) // limit,
        "files": files_list
    }

@router.get("/download/{file_id}")
@tracker.measure_async_time
async def download_file(file_id: str):
    """
    ⬇️ ดาวน์โหลดไฟล์ตาม ID
    """
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    # เชื่อมต่อกับ collection files
    files_collection = await get_collection("files")
    
    # ดึงข้อมูลไฟล์
    file_data = await files_collection.find_one({"_id": ObjectId(file_id)})
    
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