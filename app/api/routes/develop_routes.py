from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas.response_schemas import ResponseModel
from app.services.csv_service import CSVService
from app.api.dependencies import get_csv_repository
from app.utils.advanced_performance import tracker

router = APIRouter(
    prefix="/develop",
    tags=["develop"],
    responses={404: {"description": "Not Found"}}
)

@router.get("/read_and_save", response_model=ResponseModel)
@tracker.measure_async_time
async def service_1(
    csv_service: CSVService = Depends(lambda: CSVService(get_csv_repository()))
):
    """
    📊 อ่านและบันทึกข้อมูล CSV ลงฐานข้อมูล
    """
    # เรียกใช้บริการอ่านและบันทึกข้อมูล CSV
    result = await csv_service.read_and_save_csv_to_mongodb("data/sample_30k_rows.csv")
    # result = await csv_service.read_and_save_csv_to_mongodb("data/20250515-FULL-1_0.csv")
    
    # ถ้าการทำงานไม่สำเร็จให้คืนค่า HTTPException
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    # คืนค่าผลลัพธ์
    return result

@router.delete("/clear_csv", response_model=ResponseModel)
@tracker.measure_async_time
async def clear_csv(
    csv_service: CSVService = Depends(lambda: CSVService(get_csv_repository()))
):
    """
    🧹 ล้างข้อมูลทั้งหมดใน collection "csv"
    """
    # เรียกใช้บริการล้างข้อมูล
    result = await csv_service.clear_csv_collection()
    
    # ถ้าการทำงานไม่สำเร็จให้คืนค่า HTTPException
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    # คืนค่าผลลัพธ์
    return result