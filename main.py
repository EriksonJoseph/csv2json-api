from fastapi import FastAPI
import os
from dotenv import load_dotenv

# โหลด environment variables
load_dotenv()

# อ่านค่า PORT จาก environment variables
PORT = int(os.getenv("APP_PORT", 8000))

# สร้าง FastAPI application
app = FastAPI(
    title="CSV2JSON",
    description="A simple FastAPI application",
    version="1.0.0"
)

# สร้าง route สำหรับ API endpoint
@app.get("/api/hello")
async def hello_world():
    return {"message": "Hello World"}

# เพิ่ม route หลัก
@app.get("/")
async def root():
    return {"message": "Welcome to CSV2JSON API. Try /api/hello endpoint."}

# รัน server ถ้าเรียกไฟล์นี้โดยตรง
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)