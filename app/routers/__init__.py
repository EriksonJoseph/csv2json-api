from fastapi import APIRouter
from app.routers.auth.auth_router import router as auth_router
from app.routers.user.user_router import router as user_router
from app.routers.task.task_router import router as task_router
from app.routers.file.file_router import router as file_router
from app.routers.develop.develop_router import router as develop_router
from app.routers.search.search_router import router as search_router

# สร้าง APIRouter หลัก
router = APIRouter()

# รวม router ย่อยเข้าด้วยกัน
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(develop_router)
router.include_router(file_router)
router.include_router(task_router)
router.include_router(search_router)
