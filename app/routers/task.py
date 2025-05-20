from fastapi import APIRouter, Query, HTTPException, Path
from app.database import get_collection
from app.models.task import TaskCreate, TaskUpdate
from app.utils.advanced_performance import tracker
from bson import ObjectId
from datetime import datetime

router = APIRouter(
    prefix="/task",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

@router.post("/")
@tracker.measure_async_time
async def create_task(task: TaskCreate):
    """
    📋 สร้างงานใหม่
    """
    # เชื่อมต่อกับ collection tasks
    tasks_collection = await get_collection("tasks")
    
    # ตรวจสอบว่า file_id ที่อ้างถึงมีอยู่จริงหรือไม่
    files_collection = await get_collection("files")
    if not ObjectId.is_valid(task.file_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ file_id ไม่ถูกต้อง")
    
    file = await files_collection.find_one({"_id": ObjectId(task.file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="🔍 ไม่พบไฟล์ที่อ้างถึง")
    
    # เตรียมข้อมูลสำหรับบันทึก
    current_time = datetime.now()
    
    # แปลงวันที่จาก string เป็น datetime
    try:
        created_file_date = datetime.strptime(task.created_file_date, "%Y-%m-%d")
        updated_file_date = datetime.strptime(task.updated_file_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="❌ รูปแบบวันที่ไม่ถูกต้อง (ต้องเป็น YYYY-MM-DD)")
    
    task_data = {
        "topic": task.topic,
        "created_file_date": created_file_date,
        "updated_file_date": updated_file_date,
        "references": task.references,
        "file_id": task.file_id,
        "is_done_created_doc": False,  # ค่าเริ่มต้น
        "column_names": [],            # ค่าเริ่มต้น
        "error_message": None,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    # บันทึกข้อมูลลงใน MongoDB
    result = await tasks_collection.insert_one(task_data)
    
    # ดึงข้อมูลที่บันทึกแล้วกลับมาเพื่อส่งคืน
    created_task = await tasks_collection.find_one({"_id": result.inserted_id})
    
    # แปลง ObjectId เป็น string และ datetime เป็น string
    created_task["_id"] = str(created_task["_id"])
    created_task["created_file_date"] = created_task["created_file_date"].strftime("%Y-%m-%d")
    created_task["updated_file_date"] = created_task["updated_file_date"].strftime("%Y-%m-%d")
    created_task["created_at"] = created_task["created_at"].isoformat()
    created_task["updated_at"] = created_task["updated_at"].isoformat()
    
    # แปลงข้อมูลที่บันทึกให้อยู่ในรูปแบบที่เหมาะสม
    return {
        "message": "✅ สร้างงานใหม่สำเร็จ",
        "task": created_task
    }

@router.get("/")
@tracker.measure_async_time
async def get_all_tasks(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    📋 ดึงรายการงานทั้งหมด
    """
    # เชื่อมต่อกับ collection tasks
    tasks_collection = await get_collection("tasks")
    
    # คำนวณ skip สำหรับ pagination
    skip = (page - 1) * limit
    
    # นับจำนวนงานทั้งหมด
    total_tasks = await tasks_collection.count_documents({})
    
    # ดึงข้อมูลโดยมีการทำ pagination
    cursor = tasks_collection.find().sort("created_at", -1).skip(skip).limit(limit)
    tasks_list = await cursor.to_list(length=limit)
    
    # แปลง ObjectId เป็น string และ datetime เป็น string
    for task in tasks_list:
        task["_id"] = str(task["_id"])
        task["created_file_date"] = task["created_file_date"].strftime("%Y-%m-%d")
        task["updated_file_date"] = task["updated_file_date"].strftime("%Y-%m-%d")
        task["created_at"] = task["created_at"].isoformat()
        task["updated_at"] = task["updated_at"].isoformat()
    
    # ส่งคืนข้อมูลพร้อม metadata สำหรับ pagination
    return {
        "message": "📋 รายการงานทั้งหมด",
        "total": total_tasks,
        "page": page,
        "limit": limit,
        "pages": (total_tasks + limit - 1) // limit,
        "tasks": tasks_list
    }

@router.get("/{task_id}")
@tracker.measure_async_time
async def get_task(task_id: str = Path(..., description="ID ของงานที่ต้องการดึงข้อมูล")):
    """
    📝 ดึงข้อมูลงานตาม ID
    """
    # เชื่อมต่อกับ collection tasks
    tasks_collection = await get_collection("tasks")
    
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    # ดึงข้อมูลงานจาก MongoDB
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    
    # ตรวจสอบว่าพบงานหรือไม่
    if not task:
        raise HTTPException(status_code=404, detail="🔍 ไม่พบงานที่ต้องการ")
    
    # แปลง ObjectId เป็น string และ datetime เป็น string
    task["_id"] = str(task["_id"])
    task["created_file_date"] = task["created_file_date"].strftime("%Y-%m-%d")
    task["updated_file_date"] = task["updated_file_date"].strftime("%Y-%m-%d")
    task["created_at"] = task["created_at"].isoformat()
    task["updated_at"] = task["updated_at"].isoformat()
    
    # แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสมและส่งกลับ
    return {
        "message": "📝 ข้อมูลงาน",
        "task": task
    }

@router.patch("/{task_id}")
@tracker.measure_async_time
async def update_task(task_id: str, task_update: TaskUpdate):
    """
    🔄 อัปเดตข้อมูลงานตาม ID
    """
    # เชื่อมต่อกับ collection tasks
    tasks_collection = await get_collection("tasks")
    
    # ตรวจสอบความถูกต้องของ ID
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="❌ รูปแบบ ID ไม่ถูกต้อง")
    
    # ตรวจสอบว่างานมีอยู่หรือไม่
    existing_task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
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
        files_collection = await get_collection("files")
        if not ObjectId.is_valid(update_data["file_id"]):
            raise HTTPException(status_code=400, detail="❌ รูปแบบ file_id ไม่ถูกต้อง")
        
        file = await files_collection.find_one({"_id": ObjectId(update_data["file_id"])})
        if not file:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบไฟล์ที่อ้างถึง")
    
    # เพิ่ม timestamp สำหรับการอัปเดต
    update_data["updated_at"] = datetime.now()
    
    # อัปเดตข้อมูลใน MongoDB
    result = await tasks_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": update_data}
    )
    
    # ตรวจสอบว่าอัปเดตสำเร็จหรือไม่
    if result.modified_count == 0 and len(update_data) > 1:  # มีมากกว่า updated_at
        # ข้อมูลไม่มีการเปลี่ยนแปลง
        existing_task["_id"] = str(existing_task["_id"])
        existing_task["created_file_date"] = existing_task["created_file_date"].strftime("%Y-%m-%d")
        existing_task["updated_file_date"] = existing_task["updated_file_date"].strftime("%Y-%m-%d")
        existing_task["created_at"] = existing_task["created_at"].isoformat()
        existing_task["updated_at"] = existing_task["updated_at"].isoformat()
        
        return {
            "message": "ℹ️ ไม่มีการเปลี่ยนแปลงข้อมูล",
            "task": existing_task
        }
    
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