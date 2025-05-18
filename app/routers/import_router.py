from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Dict, Any
import os
from tempfile import NamedTemporaryFile
import shutil

from app.services.import_service import ImportService

router = APIRouter(
    prefix="/api/import",
    tags=["import"],
    responses={404: {"description": "Not found"}}
)

@router.post("/csv", response_model=Dict[str, Any])
async def import_csv_file(
    file: UploadFile = File(...),
    service: ImportService = Depends()
):
    """
    นำเข้าข้อมูล CSV เข้าสู่ MongoDB
    """
    # ตรวจสอบว่าเป็นไฟล์ CSV หรือไม่
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="กรุณาอัพโหลดไฟล์ CSV เท่านั้น")
    
    # บันทึกไฟล์ที่อัพโหลดมาชั่วคราว
    temp_file = NamedTemporaryFile(delete=False)
    try:
        contents = await file.read()
        with temp_file as f:
            f.write(contents)
        
        # นำเข้าข้อมูล
        result = await service.import_csv_file(temp_file.name)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการนำเข้าข้อมูล: {str(e)}")
    finally:
        # ลบไฟล์ชั่วคราว
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

@router.post("/sample", response_model=Dict[str, Any])
async def import_sample_data(
    service: ImportService = Depends()
):
    """
    นำเข้าข้อมูลตัวอย่างจากไฟล์ data/sample_100_rows.csv
    """
    result = await service.import_sample_data()
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result