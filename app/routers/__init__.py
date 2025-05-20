from fastapi import APIRouter
from app.routers import user, develop, file

# สร้าง APIRouter หลัก
router = APIRouter()

# รวม router ย่อยเข้าด้วยกัน
router.include_router(user.router)
router.include_router(develop.router)
router.include_router(file.router)