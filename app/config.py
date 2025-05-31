from pydantic import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # ตั้งค่าพื้นฐาน
    APP_NAME: str = "CSV2JSON"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8000
    
    # ตั้งค่า MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "csv2json"
    
    # JWT settings
    JWT_SECRET_KEY: str = "fallback-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_SECRET_KEY: str = "fallback-refresh-secret-key"
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440
    
    class Config:
        env_file = ".env"  # อ่านค่าจากไฟล์ .env
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    # ตรวจสอบและรีโหลด settings ถ้ามีการเปลี่ยนแปลงในไฟล์ .env
    if os.path.exists(".env"):
        os.environ.pop("MONGODB_URI", None)  # ลบค่าเก่า
    return Settings()