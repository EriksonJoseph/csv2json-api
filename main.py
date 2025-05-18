from fastapi import FastAPI

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