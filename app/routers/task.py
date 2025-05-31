from fastapi import APIRouter, Query, Path, Depends
from app.services.task_service import TaskService
from app.repositories.task_repository import TaskRepository
from app.repositories.file_repository import FileRepository
from app.models.task import TaskCreate, TaskUpdate
from app.utils.advanced_performance import tracker
from app.workers.background_worker import get_current_processing_task
from app.dependencies.auth import require_user

router = APIRouter(
    prefix="/task",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

# Initialize repositories and service
task_repository = TaskRepository()
file_repository = FileRepository()
task_service = TaskService(task_repository, file_repository)

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
    return await task_service.create_task(task)

@router.get("/")
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
    print("hello torpong!!")
    """
    🔄 อัปเดตข้อมูลงานตาม ID
    """
    return await task_service.update_task(task_id, task_update)

@router.delete("/{task_id}")
@tracker.measure_async_time
async def delete_task(task_id: str = Path(..., description="ID ของงานที่ต้องการลบ"), current_user = Depends(require_user)):
    """
    ลบงานตาม ID
    """
    return await task_service.delete_task(task_id)