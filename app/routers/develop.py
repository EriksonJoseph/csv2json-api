from fastapi import APIRouter, Query, HTTPException, Path
from app.services.csv_service import read_and_save_csv_to_mongodb, clear_csv_collection
from app.utils.advanced_performance import tracker

router = APIRouter(
  prefix="/develop",
  tags=["develop"],
  responses={404: { "description": "Not Found"}}
)

@router.get("/read_and_save")
@tracker.measure_async_time
async def service_1():
  # เรียกใช้บริการอ่านและบันทึกข้อมูล CSV
  # result = await read_and_save_csv_to_mongodb("data/sample_30k_rows.csv")
  result = await read_and_save_csv_to_mongodb()
  
  # ถ้าการทำงานไม่สำเร็จให้คืนค่า HTTPException
  if not result["success"]:
    raise HTTPException(status_code=500, detail=result["message"])
  
  # คืนค่าผลลัพธ์
  return result

@router.delete("/clear_csv")
@tracker.measure_async_time
async def clear_csv():
  """
  ล้างข้อมูลทั้งหมดใน collection "csv"
  """
  # เรียกใช้บริการล้างข้อมูล
  result = await clear_csv_collection()
  
  # ถ้าการทำงานไม่สำเร็จให้คืนค่า HTTPException
  if not result["success"]:
    raise HTTPException(status_code=500, detail=result["message"])
  
  # คืนค่าผลลัพธ์
  return result