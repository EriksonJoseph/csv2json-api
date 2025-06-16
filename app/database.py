from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("database")



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
async def initialize_db() -> bool:
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB]

        # สร้างดัชนีสำหรับคอลเลกชัน users
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        
        # สร้างดัชนีสำหรับคอลเลกชัน files
        await db.files.create_index("filename", unique=True)
        await db.files.create_index("upload_date")

        # ตรวจสอบและสร้าง admin user ถ้าไม่มี
        admin_user = await db.users.find_one({"username": "admin"})
        if not admin_user:
            # Import AuthService here to avoid circular import
            from app.routers.auth.auth_service import AuthService
            auth_service = AuthService()
            
            admin_data: Dict[str, Any] = {
                "username": "admin",
                "password": auth_service.get_password_hash("ThisIsAdmin"),
                "email": "admin@email.com",
                "first_name": "adminFirstName",
                "last_name": "adminLastname",
                "middle_name": "adminMiddleName",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "last_login_ip": None,
                "login_history": [],
                "roles": ["admin"]
            }
            await db.users.insert_one(admin_data)
            logger.info("👤 สร้าง admin user เริ่มต้นสำเร็จ (username: admin)")
        else:
            logger.info("👤 มี admin user อยู่แล้ว")

        logger.info(f"✅ เชื่อมต่อ MongoDB สำเร็จ: {settings.MONGODB_URI}")
        return True
    except Exception as e:
        logger.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ MongoDB: {str(e)}")
        return False