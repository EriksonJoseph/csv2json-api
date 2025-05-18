from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time

from app.config import get_settings
from app.database import initialize_db
from app.routers import router

# เรียกใช้งาน settings
settings = get_settings()

# print(f"🚀🚀🚀🚀🚀🚀 Hello developer 🚀🚀🚀🚀🚀🚀")

# print(f"⚙️⚙️⚙️⚙️  Creating FastAPI application")
# สร้าง FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="RESTful API for CSV2JSON",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)
# print(f"🎉🎉🎉🎉  Done Creating FastAPI application")

# print("⚙️⚙️⚙️⚙️  Adding CORS middleware")
# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ในโปรดักชันควรระบุ domain ที่อนุญาตเท่านั้น
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# print(f"🎉🎉🎉🎉  Done Adding CORS middleware")

# print("⚙️⚙️⚙️⚙️  Adding Time process log")
# เพิ่ม middleware สำหรับบันทึกเวลาที่ใช้ในการประมวลผล
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# print(f"🎉🎉🎉🎉  Done Adding Time process log")

# print("⚙️⚙️⚙️⚙️  Adding Application router")
# เพิ่ม router หลัก
app.include_router(router, prefix="/api")

# สร้าง route หลัก
@app.get("/")
async def root():
    return {
        "message": f"ยินดีต้อนรับสู่ {settings.APP_NAME} API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }
# print(f"🎉🎉🎉🎉  Done Adding Application router")


# จัดการ startup event
@app.on_event("startup")
async def startup_event():
    # print("On Start up event")
    # เชื่อมต่อกับ MongoDB
    # print("⚙️⚙️⚙️⚙️  Initializing Database")
    initialize_db()
    # print("🎉🎉🎉🎉  Done Initializing Database")

# จัดการ shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # print("On Shutdown event")
    # ทำความสะอาดทรัพยากรต่างๆ ถ้าจำเป็น
    pass

# รัน server ถ้าเรียกไฟล์นี้โดยตรง
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)