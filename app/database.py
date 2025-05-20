from pymongo import MongoClient
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient

# สร้างตัวแปร global เพื่อเก็บ client ไว้ใช้งานต่อ
_client = None

settings = get_settings()

async def get_client():
    global _client
    if _client is None:
        # คอนฟิกการเชื่อมต่อ (ปรับตามความเหมาะสม)
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=30000
        )
    return _client

async def get_database():
    client = await get_client()
    return client[settings.MONGODB_DB]
    
async def get_collection(collection_name: str):
    db = await get_database()
    return db[collection_name]

# เชื่อมต่อ MongoDB และเตรียม collection สำหรับ Entity
async def initialize_db():
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB]

        # สร้างดัชนีสำหรับคอลเลกชัน users
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        
        # สร้างดัชนีสำหรับคอลเลกชัน files
        await db.files.create_index("filename", unique=True)
        await db.files.create_index("upload_date")

        print(f"✅ เชื่อมต่อ MongoDB สำเร็จ: {settings.MONGODB_URI}")
        return True
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ MongoDB: {str(e)}")
        return False