from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, Path
from fastapi.responses import FileResponse
from app.api.schemas.file_schemas import FileResponse
from app.api.schemas.response_schemas import ResponseModel, PaginatedResponse
from app.services.file_service import FileService
from app.api.dependencies import get_file_repository
from app.utils.advanced_performance import tracker
from bson import ObjectId
from typing import List

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not Found"}}
)

@router.post("/upload", response_model=ResponseModel[FileResponse])
@tracker.measure_async_time
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileService = Depends(lambda: FileService(get_file_repository()))
):
    """
    🚀 อัปโหลดไฟล์และบันทึกลงโฟลเดอร์ temp พร้อมบันทึกข้อมูลลง collection files
    """
    try:
        # ตรวจสอบว่ามีไฟล์หรือไม่
        if not file.filename:
            raise HTTPException(status_code=400, detail="⚠️ ไม่พบไฟล์ที่อัปโหลด")
            
        result = await file_service.save_file(file)
        
        return ResponseModel(
            message="✅ อัปโหลดไฟล์สำเร็จ",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ เกิดข้อผิดพลาดในการอัปโหลดไฟล์: {str(e)}")

@router.get("/", response_model=PaginatedResponse[List[FileResponse]])
@tracker.measure_async_time
async def get_all_files(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    file_service: FileService = Depends(lambda: FileService(get_file_repository()))
):
    """
    📋 ดึงรายการไฟล์ทั้งหมด
    """
    result = await file_service.get_all_files(page, limit)
    return result

@router.get("/download/{file_id}")
@tracker.measure_async_time
async def download_file(
    file_id: str,
    file_service: FileService = Depends(lambda: FileService(get_file_repository()))
):
    """
    ⬇️ ดาวน์โหลดไฟล์ตาม ID
    """
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    return await file_service.download_file(file_id)