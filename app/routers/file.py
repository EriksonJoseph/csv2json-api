from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import FileResponse
from app.services.file_service import FileService
from app.repositories.file_repository import FileRepository
from app.utils.advanced_performance import tracker

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not Found"}}
)

# Initialize repository and service
file_repository = FileRepository()
file_service = FileService(file_repository)

@router.post("/upload")
@tracker.measure_async_time
async def upload_file(file: UploadFile = File(...)):
    """
    🚀 อัปโหลดไฟล์และบันทึกลงโฟลเดอร์ temp พร้อมบันทึกข้อมูลลง collection files
    """
    return await file_service.upload_file(file)

@router.get("/")
@tracker.measure_async_time
async def get_all_files(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    📋 ดึงรายการไฟล์ทั้งหมด
    """
    return await file_service.get_all_files(page, limit)

@router.get("/download/{file_id}")
@tracker.measure_async_time
async def download_file(file_id: str):
    """
    ⬇️ ดาวน์โหลดไฟล์ตาม ID
    """
    return await file_service.download_file(file_id)