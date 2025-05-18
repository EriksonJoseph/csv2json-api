from fastapi import APIRouter
from app.routers import entity, import

# สร้าง APIRouter หลัก
router = APIRouter()

# รวม router ย่อยเข้าด้วยกัน
router.include_router(entity.router)
router.include_router(import.router)