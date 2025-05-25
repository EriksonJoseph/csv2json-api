from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.auth import UserRole

class LoginHistory(BaseModel):
    user_id: str
    username: str
    ip_address: str
    login_at: datetime
    status: str  # success/failure
    reason: Optional[str] = None

class LoginAttempt(BaseModel):
    user_id: str
    username: str
    attempts: int
    last_attempt: datetime
    locked_until: Optional[datetime] = None
    ip_address: str

class LoginSettings(BaseModel):
    max_attempts: int = 5  # จำนวนครั้งที่ลอง login ได้ก่อนจะถูกล็อก
    lock_duration_minutes: int = 30  # ระยะเวลาที่จะถูกล็อก (นาที)
    reset_duration_minutes: int = 60  # ระยะเวลาที่จะรีเซ็ตการลอง login (นาที)
