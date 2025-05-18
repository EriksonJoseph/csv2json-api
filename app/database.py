from pymongo import MongoClient
from app.config import get_settings

settings = get_settings()
print("📂 📂 📂 📂 📂 📂 📂 📂 📂 📂 📂 📂 at database py setting")

# ฟังก์ชันสำหรับเชื่อมต่อ MongoDB
def get_database():
    client = MongoClient(settings.MONGODB_URI)
    return client[settings.MONGODB_DB]

# ฟังก์ชันสำหรับเรียกใช้ collection ใน MongoDB
def get_collection(collection_name: str):
    db = get_database()
    return db[collection_name]

# เชื่อมต่อ MongoDB และเตรียม collection สำหรับ Entity
def initialize_db():
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB]
        print(f"✅ เชื่อมต่อ MongoDB สำเร็จ: {settings.MONGODB_URI}")
        client.close()
        return True
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ MongoDB: {str(e)}")
        return False