from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time

from app.config import get_settings
from app.database import initialize_db
from app.routers import router
from app.utils.advanced_performance import tracker  # นำเข้า tracker

# เรียกใช้งาน settings
settings = get_settings()

# สร้าง FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="RESTful API for CSV2JSON",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ในโปรดักชันควรระบุ domain ที่อนุญาตเท่านั้น
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# เพิ่ม middleware สำหรับบันทึกเวลาที่ใช้ในการประมวลผล
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# เพิ่ม router หลัก
app.include_router(router, prefix="/api")

# สร้าง route สำหรับดู performance statistics
@app.get("/api/performance")
async def get_performance_stats():
    stats = tracker.get_stats()
    return stats

# สร้าง route หลัก
@app.get("/")
async def root():
    return {
        "message": f"ยินดีต้อนรับสู่ {settings.APP_NAME} API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }

# จัดการ startup event
@app.on_event("startup")
async def startup_event():
    # เชื่อมต่อกับ MongoDB
    await initialize_db()

# จัดการ shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # บันทึกข้อมูล performance ก่อนปิด app
    try:
        tracker.export_to_json("logs/performance_final.json")
    except Exception as e:
        print(f"Error exporting performance data: {e}")
    
    # ทำความสะอาดทรัพยากรต่างๆ ถ้าจำเป็น
    pass

# รัน server ถ้าเรียกไฟล์นี้โดยตรง
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)