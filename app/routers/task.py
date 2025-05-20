from fastapi import APIRouter, Query, HTTPException, Path
from app.services.task_service import TaskService
from app.repositories.task_repository import TaskRepository
from app.repositories.file_repository import FileRepository
from app.models.task import TaskCreate, TaskUpdate
from app.utils.advanced_performance import tracker
from app.exceptions import TaskException

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
    try:
        created_task = await task_service.create_task(task)
        return {
            "message": "✅ สร้างงานใหม่สำเร็จ",
            "task": created_task
        }
    except TaskException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.get("/")
@tracker.measure_async_time
async def get_all_tasks(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    📋 ดึงรายการงานทั้งหมด
    """
    try:
        result = await task_service.get_all_tasks(page, limit)
        return {
            "tasks": result["tasks"],
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"]
        }
    except TaskException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.get("/{task_id}")
@tracker.measure_async_time
async def get_task(task_id: str = Path(..., description="ID ของงานที่ต้องการดึงข้อมูล")):
    """
    📝 ดึงข้อมูลงานตาม ID
    """
    try:
        task = await task_service.get_task_by_id(task_id)
        if not task:
            raise TaskException("Task not found", status_code=404)
        return {
            "message": "✅ ดึงข้อมูลงานสำเร็จ",
            "task": task
        }
    except TaskException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.put("/{task_id}")
@tracker.measure_async_time
async def update_task(task_id: str, task_update: TaskUpdate):
    """
    🔄 อัปเดตข้อมูลงานตาม ID
    """
    try:
        updated_task = await task_service.update_task(task_id, task_update)
        return {
            "message": "✅ อัปเดตข้อมูลงานสำเร็จ",
            "task": updated_task
        }
    except TaskException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    # ดึงข้อมูลที่อัปเดตแล้ว
    updated_task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    
    # แปลง ObjectId เป็น string และ datetime เป็น string
    updated_task["_id"] = str(updated_task["_id"])
    updated_task["created_file_date"] = updated_task["created_file_date"].strftime("%Y-%m-%d")
    updated_task["updated_file_date"] = updated_task["updated_file_date"].strftime("%Y-%m-%d")
    updated_task["created_at"] = updated_task["created_at"].isoformat()
    updated_task["updated_at"] = updated_task["updated_at"].isoformat()
    
    # ส่งข้อมูลที่อัปเดตแล้วกลับไป
    return {
        "message": "✅ อัปเดตข้อมูลงานสำเร็จ",
        "task": updated_task
    }

@router.delete("/{task_id}")
@tracker.measure_async_time
async def delete_task(task_id: str = Path(..., description="ID ของงานที่ต้องการลบ")):
    """
    🗑️ ลบงานตาม ID
    """
    # เชื่อมต่อกับ collection tasks
    tasks_collection = await get_collection("tasks")
    
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    # หาข้อมูลงานก่อนลบเพื่อเก็บไว้แสดงผล
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    
    # ตรวจสอบว่าพบงานหรือไม่
    if not task:
        raise HTTPException(status_code=404, detail="🔍 ไม่พบงานที่ต้องการลบ")
    
    # ลบข้อมูลงานจาก MongoDB
    result = await tasks_collection.delete_one({"_id": ObjectId(task_id)})
    
    # ตรวจสอบว่าลบสำเร็จหรือไม่
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="⚠️ เกิดข้อผิดพลาดในการลบข้อมูล")
    
    # แปลง ObjectId เป็น string และ datetime เป็น string
    task["_id"] = str(task["_id"])
    task["created_file_date"] = task["created_file_date"].strftime("%Y-%m-%d")
    task["updated_file_date"] = task["updated_file_date"].strftime("%Y-%m-%d")
    task["created_at"] = task["created_at"].isoformat()
    task["updated_at"] = task["updated_at"].isoformat()
    
    # แปลงข้อมูลที่ถูกลบและส่งกลับ
    return {
        "message": "🗑️ ลบข้อมูลงานสำเร็จ",
        "deleted_task": task
    }