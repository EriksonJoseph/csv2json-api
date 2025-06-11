from fastapi import APIRouter, Query, Path, Depends
from app.routers.task.task_service import TaskService
from app.routers.task.task_model import TaskCreate, TaskUpdate
from app.utils.advanced_performance import tracker
from app.workers.background_worker import get_current_processing_task
from app.dependencies.auth import require_user
from app.api.schemas import PaginationResponse
from typing import Dict, Any

router = APIRouter(
    prefix="/task",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

# Initialize service
task_service = TaskService()

@router.get("/current-processing")
@tracker.measure_async_time
async def get_current_task_processing(current_user = Depends(require_user)):
    """
    🔄 ดูงานที่กำลังถูกประมวลผลอยู่
    """
    return await get_current_processing_task()

@router.post("/")
@tracker.measure_async_time
async def create_task(task: TaskCreate, current_user = Depends(require_user)):
    """
    📋 สร้างงานใหม่
    """
    return await task_service.create_task(task, current_user.user_id)

@router.get("/", response_model=PaginationResponse[Dict[str, Any]])
@tracker.measure_async_time
async def get_all_tasks(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), current_user = Depends(require_user)):
    """
    📋 ดึงรายการงานทั้งหมด
    """
    return await task_service.get_all_tasks(page, limit)

@router.get("/{task_id}")
@tracker.measure_async_time
async def get_task(task_id: str = Path(..., description="ID ของงานที่ต้องการดึงข้อมูล"), current_user = Depends(require_user)):
    """
    📝 ดึงข้อมูลงานตาม ID
    """
    return await task_service.get_task_by_id(task_id)

@router.put("/{task_id}")
@tracker.measure_async_time
async def update_task(task_id: str, task_update: TaskUpdate, current_user = Depends(require_user)):
    """
    🔄 อัปเดตข้อมูลงานตาม ID
    """
    return await task_service.update_task(task_id, task_update, current_user.user_id)

@router.delete("/{task_id}")
@tracker.measure_async_time
async def delete_task(task_id: str = Path(..., description="ID ของงานที่ต้องการลบ"), current_user = Depends(require_user)):
    """
    ลบงานตาม ID
    """
    return await task_service.delete_task(task_id)
