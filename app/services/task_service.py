"""
Task Service

ดำเนินการเกี่ยวกับงาน
"""
from fastapi import HTTPException
from datetime import datetime
from app.repositories.task_repository import TaskRepository
from app.repositories.file_repository import FileRepository
from app.api.schemas.task_schemas import TaskCreate, TaskUpdate, TaskResponse
from app.api.schemas.response_schemas import ResponseModel, PaginatedResponse
from app.utils.advanced_performance import tracker
from bson import ObjectId
from typing import Dict, Any, List

class TaskService:
    """
    Service สำหรับจัดการงาน
    """
    def __init__(self, task_repository: TaskRepository, file_repository: FileRepository):
        self.task_repository = task_repository
        self.file_repository = file_repository
    
    @tracker.measure_async_time
    async def create_task(self, task_data: TaskCreate) -> ResponseModel:
        """
        สร้างงานใหม่
        """
        # ตรวจสอบว่า file_id ที่อ้างถึงมีอยู่จริงหรือไม่
        if not ObjectId.is_valid(task_data.file_id):
            raise HTTPException(status_code=400, detail="❌ รูปแบบ file_id ไม่ถูกต้อง")
        
        file = await self.file_repository.find_by_id(task_data.file_id)
        if not file:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบไฟล์ที่อ้างถึง")
        
        # แปลงวันที่จาก string เป็น datetime
        try:
            created_file_date = datetime.strptime(task_data.created_file_date, "%Y-%m-%d")
            updated_file_date = datetime.strptime(task_data.updated_file_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="❌ รูปแบบวันที่ไม่ถูกต้อง (ต้องเป็น YYYY-MM-DD)")
        
        # เตรียมข้อมูลสำหรับบันทึก
        task_dict = {
            "topic": task_data.topic,
            "created_file_date": created_file_date,
            "updated_file_date": updated_file_date,
            "references": task_data.references,
            "file_id": task_data.file_id,
            "is_done_created_doc": False,  # ค่าเริ่มต้น
            "column_names": [],            # ค่าเริ่มต้น
            "error_message": None
        }
        
        # บันทึกข้อมูลลงใน MongoDB
        created_task = await self.task_repository.create(task_dict)
        
        # แปลง ObjectId เป็น string และ datetime เป็น string
        task_dict = {**created_task}
        task_dict["id"] = str(task_dict.pop("_id"))
        if isinstance(task_dict["created_file_date"], datetime):
            task_dict["created_file_date"] = task_dict["created_file_date"].strftime("%Y-%m-%d")
        if isinstance(task_dict["updated_file_date"], datetime):
            task_dict["updated_file_date"] = task_dict["updated_file_date"].strftime("%Y-%m-%d")
        if isinstance(task_dict["created_at"], datetime):
            task_dict["created_at"] = task_dict["created_at"].isoformat()
        if isinstance(task_dict["updated_at"], datetime):
            task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        
        return ResponseModel(
            message="✅ สร้างงานใหม่สำเร็จ",
            data=task_dict
        )
    
    @tracker.measure_async_time
    async def get_all_tasks(self, page: int, limit: int) -> PaginatedResponse:
        """
        ดึงรายการงานทั้งหมด
        """
        # คำนวณ skip สำหรับ pagination
        skip = (page - 1) * limit
        
        # นับจำนวนงานทั้งหมด
        total_tasks = await self.task_repository.count()
        
        # ดึงข้อมูลโดยมีการทำ pagination
        tasks_list = await self.task_repository.find_all(skip, limit)
        
        # แปลง ObjectId เป็น string และ datetime เป็น string
        tasks = []
        for task in tasks_list:
            task_dict = {**task}
            task_dict["id"] = str(task_dict.pop("_id"))
            if isinstance(task_dict["created_file_date"], datetime):
                task_dict["created_file_date"] = task_dict["created_file_date"].strftime("%Y-%m-%d")
            if isinstance(task_dict["updated_file_date"], datetime):
                task_dict["updated_file_date"] = task_dict["updated_file_date"].strftime("%Y-%m-%d")
            if isinstance(task_dict["created_at"], datetime):
                task_dict["created_at"] = task_dict["created_at"].isoformat()
            if isinstance(task_dict["updated_at"], datetime):
                task_dict["updated_at"] = task_dict["updated_at"].isoformat()
            tasks.append(task_dict)
        
        return PaginatedResponse(
            message="📋 รายการงานทั้งหมด",
            total=total_tasks,
            page=page,
            limit=limit,
            pages=(total_tasks + limit - 1) // limit,
            data=tasks
        )
    
    @tracker.measure_async_time
    async def get_task(self, task_id: str) -> ResponseModel:
        """
        ดึงข้อมูลงานตาม ID
        """
        # ดึงข้อมูลงานจาก MongoDB
        task = await self.task_repository.find_by_id(task_id)
        
        # ตรวจสอบว่าพบงานหรือไม่
        if not task:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบงานที่ต้องการ")
        
        # แปลง ObjectId เป็น string และ datetime เป็น string
        task_dict = {**task}
        task_dict["id"] = str(task_dict.pop("_id"))
        if isinstance(task_dict["created_file_date"], datetime):
            task_dict["created_file_date"] = task_dict["created_file_date"].strftime("%Y-%m-%d")
        if isinstance(task_dict["updated_file_date"], datetime):
            task_dict["updated_file_date"] = task_dict["updated_file_date"].strftime("%Y-%m-%d")
        if isinstance(task_dict["created_at"], datetime):
            task_dict["created_at"] = task_dict["created_at"].isoformat()
        if isinstance(task_dict["updated_at"], datetime):
            task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        
        return ResponseModel(
            message="📝 ข้อมูลงาน",
            data=task_dict
        )
    
    @tracker.measure_async_time
    async def update_task(self, task_id: str, task_update: TaskUpdate) -> ResponseModel:
        """
        อัปเดตข้อมูลงานตาม ID
        """
        # ตรวจสอบว่างานมีอยู่หรือไม่
        existing_task = await self.task_repository.find_by_id(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบงานที่ต้องการอัปเดต")
        
        # สร้าง dict สำหรับเก็บข้อมูลที่จะอัปเดต
        update_data = {}
        
        # เพิ่มเฉพาะฟิลด์ที่ไม่ใช่ None ลงใน update_data
        task_dict = task_update.dict(exclude_unset=True)
        for field, value in task_dict.items():
            if value is not None:
                # แปลงวันที่จาก string เป็น datetime ถ้าจำเป็น
                if field == "created_file_date" or field == "updated_file_date":
                    try:
                        update_data[field] = datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        raise HTTPException(status_code=400, detail=f"❌ รูปแบบวันที่ {field} ไม่ถูกต้อง (ต้องเป็น YYYY-MM-DD)")
                else:
                    update_data[field] = value
        
        # ถ้าไม่มีข้อมูลที่จะอัปเดตให้แจ้งเตือน
        if not update_data:
            raise HTTPException(status_code=400, detail="⚠️ ไม่มีข้อมูลที่จะอัปเดต")
        
        # ถ้ามีการอัปเดต file_id ให้ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        if "file_id" in update_data:
            if not ObjectId.is_valid(update_data["file_id"]):
                raise HTTPException(status_code=400, detail="❌ รูปแบบ file_id ไม่ถูกต้อง")
            
            file = await self.file_repository.find_by_id(update_data["file_id"])
            if not file:
                raise HTTPException(status_code=404, detail="🔍 ไม่พบไฟล์ที่อ้างถึง")
        
        # อัปเดตข้อมูลใน MongoDB
        updated_task = await self.task_repository.update(task_id, update_data)
        
        # ตรวจสอบว่าอัปเดตสำเร็จหรือไม่
        if updated_task is None:
            # ข้อมูลไม่มีการเปลี่ยนแปลง
            existing_task_dict = {**existing_task}
            existing_task_dict["id"] = str(existing_task_dict.pop("_id"))
            if isinstance(existing_task_dict["created_file_date"], datetime):
                existing_task_dict["created_file_date"] = existing_task_dict["created_file_date"].strftime("%Y-%m-%d")
            if isinstance(existing_task_dict["updated_file_date"], datetime):
                existing_task_dict["updated_file_date"] = existing_task_dict["updated_file_date"].strftime("%Y-%m-%d")
            if isinstance(existing_task_dict["created_at"], datetime):
                existing_task_dict["created_at"] = existing_task_dict["created_at"].isoformat()
            if isinstance(existing_task_dict["updated_at"], datetime):
                existing_task_dict["updated_at"] = existing_task_dict["updated_at"].isoformat()
            
            return ResponseModel(
                message="ℹ️ ไม่มีการเปลี่ยนแปลงข้อมูล",
                data=existing_task_dict
            )
        
        # แปลง ObjectId เป็น string และ datetime เป็น string
        updated_task_dict = {**updated_task}
        updated_task_dict["id"] = str(updated_task_dict.pop("_id"))
        if isinstance(updated_task_dict["created_file_date"], datetime):
            updated_task_dict["created_file_date"] = updated_task_dict["created_file_date"].strftime("%Y-%m-%d")
        if isinstance(updated_task_dict["updated_file_date"], datetime):
            updated_task_dict["updated_file_date"] = updated_task_dict["updated_file_date"].strftime("%Y-%m-%d")
        if isinstance(updated_task_dict["created_at"], datetime):
            updated_task_dict["created_at"] = updated_task_dict["created_at"].isoformat()
        if isinstance(updated_task_dict["updated_at"], datetime):
            updated_task_dict["updated_at"] = updated_task_dict["updated_at"].isoformat()
        
        return ResponseModel(
            message="✅ อัปเดตข้อมูลงานสำเร็จ",
            data=updated_task_dict
        )
    
    @tracker.measure_async_time
    async def delete_task(self, task_id: str) -> ResponseModel:
        """
        ลบงานตาม ID
        """
        # ลบข้อมูลงานจาก MongoDB
        deleted_task = await self.task_repository.delete(task_id)
        
        # ตรวจสอบว่าลบสำเร็จหรือไม่
        if not deleted_task:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบงานที่ต้องการลบ")
        
        # แปลง ObjectId เป็น string และ datetime เป็น string
        task_dict = {**deleted_task}
        task_dict["id"] = str(task_dict.pop("_id"))
        if isinstance(task_dict["created_file_date"], datetime):
            task_dict["created_file_date"] = task_dict["created_file_date"].strftime("%Y-%m-%d")
        if isinstance(task_dict["updated_file_date"], datetime):
            task_dict["updated_file_date"] = task_dict["updated_file_date"].strftime("%Y-%m-%d")
        if isinstance(task_dict["created_at"], datetime):
            task_dict["created_at"] = task_dict["created_at"].isoformat()
        if isinstance(task_dict["updated_at"], datetime):
            task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        
        return ResponseModel(
            message="🗑️ ลบข้อมูลงานสำเร็จ",
            data=task_dict
        )