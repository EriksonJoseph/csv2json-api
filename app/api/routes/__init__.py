from fastapi import APIRouter
from app.api.routes import user_routes, file_routes, task_routes, develop_routes

# สร้าง APIRouter หลัก
router = APIRouter()

# รวม router ย่อยเข้าด้วยกัน
router.include_router(user_routes.router)
router.include_router(file_routes.router)
router.include_router(task_routes.router)
router.include_router(develop_routes.router)