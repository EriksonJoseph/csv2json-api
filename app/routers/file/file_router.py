from fastapi import APIRouter, UploadFile, File, Query, Depends, Form
from fastapi.responses import FileResponse
from app.routers.file.file_service import FileService
from app.routers.file.file_model import InitiateUploadRequest
from app.utils.advanced_performance import tracker
from app.dependencies.auth import require_user
from app.api.schemas import PaginationResponse
from typing import Dict, Any

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not Found"}}
)

# Initialize service
file_service = FileService()

@router.post("/upload")
@tracker.measure_async_time
async def upload_file(file: UploadFile = File(...), current_user = Depends(require_user)):
    """
    🚀 อัปโหลดไฟล์และบันทึกลงโฟลเดอร์ temp พร้อมบันทึกข้อมูลลง collection files
    """
    return await file_service.upload_file(file)

@router.get("/", response_model=PaginationResponse[Dict[str, Any]])
@tracker.measure_async_time
async def get_all_files(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), current_user = Depends(require_user)):
    """
    📋 ดึงรายการไฟล์ทั้งหมด
    """
    return await file_service.get_all_files(page, limit)

@router.get("/{file_id}")
@tracker.measure_async_time
async def get_file(file_id: str, current_user = Depends(require_user)):
    """
    📝 ดึงข้อมูลไฟล์ตาม ID
    """
    return await file_service.get_file_by_id(file_id)

@router.delete("/{file_id}")
@tracker.measure_async_time
async def delete_file(file_id: str, current_user = Depends(require_user)):
    """
    🗑️ ลบไฟล์ตาม ID
    """
    return await file_service.delete_file(file_id)

@router.get("/download/{file_id}")
@tracker.measure_async_time
async def download_file(file_id: str, current_user = Depends(require_user)) -> FileResponse:
    """
    ⬇️ ดาวน์โหลดไฟล์ตาม ID
    """
    return await file_service.download_file(file_id)

@router.post("/chunked/initiate")
@tracker.measure_async_time
async def initiate_chunked_upload(request: InitiateUploadRequest, current_user = Depends(require_user)):
    """
    🚀 เริ่มต้น chunked upload สำหรับไฟล์ขนาดใหญ่
    """
    return await file_service.initiate_chunked_upload(request)

@router.post("/chunked/{upload_id}/chunk")
@tracker.measure_async_time
async def upload_chunk(
    upload_id: str,
    chunk_number: int = Form(...),
    chunk: UploadFile = File(...),
    current_user = Depends(require_user)
):
    """
    📦 อัปโหลด chunk ของไฟล์
    """
    return await file_service.upload_chunk(upload_id, chunk_number, chunk)

@router.get("/chunked/{upload_id}/status")
@tracker.measure_async_time
async def get_chunked_upload_status(upload_id: str, current_user = Depends(require_user)):
    """
    📊 ตรวจสอบสถานะการอัปโหลดแบบ chunked
    """
    return await file_service.get_chunked_upload_status(upload_id)

@router.delete("/chunked/{upload_id}")
@tracker.measure_async_time
async def cancel_chunked_upload(upload_id: str, current_user = Depends(require_user)):
    """
    ❌ ยกเลิกการอัปโหลดแบบ chunked
    """
    return await file_service.cancel_chunked_upload(upload_id)
