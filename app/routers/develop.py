from fastapi import APIRouter, Depends
from app.services.csv_service import read_and_save_csv_to_mongodb, clear_csv_collection
from app.utils.advanced_performance import tracker
from app.dependencies.auth import require_admin

router = APIRouter(
  prefix="/develop",
  tags=["develop"],
  responses={404: { "description": "Not Found"}}
)

@router.get("/")
@tracker.measure_time
def health(current_user = Depends(require_admin)):
  """
  🏠 ตรวจสอบว่าสามารถเรียก API ได้หรือไม่
  """
  return {"status": "ok"}

@router.get("/read_and_save")
@tracker.measure_async_time
async def read_and_save(current_user = Depends(require_admin)):
  """
  อ่านและบันทึกข้อมูล CSV
  """
  return await read_and_save_csv_to_mongodb("data/sample_30k_rows.csv")

@router.delete("/clear_csv")
@tracker.measure_async_time
async def clear_csv(current_user = Depends(require_admin)):
  """
  ล้างข้อมูลทั้งหมดใน collection "csv"
  """
  return await clear_csv_collection()