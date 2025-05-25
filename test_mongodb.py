from pymongo import MongoClient
import os
from app.config import get_settings

async def test_mongodb_connection():
    settings = get_settings()
    print(f"Testing MongoDB connection with URI: {settings.MONGODB_URI}")
    
    try:
        # สร้าง client
        client = MongoClient(settings.MONGODB_URI)
        
        # ทดสอบการเชื่อมต่อ
        db = client[settings.MONGODB_DB]
        print("Attempting to connect...")
        
        # ลองใช้ command ง่ายๆ เพื่อทดสอบการเชื่อมต่อ
        db.command("ping")
        print("✅ Connected successfully!")
        
        # แสดงข้อมูล server
        print("\nServer Information:")
        print(f"Server version: {client.server_info()['version']}")
        print(f"Database: {settings.MONGODB_DB}")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        
    finally:
        # ปิดการเชื่อมต่อ
        client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_mongodb_connection())
