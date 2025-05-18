from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # ตั้งค่าพื้นฐาน
    APP_NAME: str = "CSV2JSON"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8000
    
    # ตั้งค่า MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "csv2json"
    
    class Config:
        env_file = ".env"  # อ่านค่าจากไฟล์ .env
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()