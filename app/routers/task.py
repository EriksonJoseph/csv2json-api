from fastapi import APIRouter, Query, Path
from app.services.task_service import TaskService
from app.repositories.task_repository import TaskRepository
from app.repositories.file_repository import FileRepository
from app.models.task import TaskCreate, TaskUpdate
from app.utils.advanced_performance import tracker

router = APIRouter(
    prefix="/task",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

# Initialize repositories and service
task_repository = TaskRepository()
file_repository = FileRepository()
task_service = TaskService(task_repository, file_repository)

@router.post("/")
@tracker.measure_async_time
async def create_task(task: TaskCreate):
    """
    📋 สร้างงานใหม่
    """
    return await task_service.create_task(task)

@router.get("/")
@tracker.measure_async_time
async def get_all_tasks(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    📋 ดึงรายการงานทั้งหมด
    """
    return await task_service.get_all_tasks(page, limit)

@router.get("/{task_id}")
@tracker.measure_async_time
async def get_task(task_id: str = Path(..., description="ID ของงานที่ต้องการดึงข้อมูล")):
    """
    📝 ดึงข้อมูลงานตาม ID
    """
    return await task_service.get_task_by_id(task_id)

@router.put("/{task_id}")
@tracker.measure_async_time
async def update_task(task_id: str, task_update: TaskUpdate):
    print("hello torpong!!")
    """
    🔄 อัปเดตข้อมูลงานตาม ID
    """
    return await task_service.update_task(task_id, task_update)

@router.delete("/{task_id}")
@tracker.measure_async_time
async def delete_task(task_id: str = Path(..., description="ID ของงานที่ต้องการลบ")):
    """
    ลบงานตาม ID
    """
    return await task_service.delete_task(task_id)