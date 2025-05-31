from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: List[str] = []

class RefreshToken(BaseModel):
    user_id: str
    token: str
    expires_at: Optional[datetime] = None
    ip_address: str
    user_agent: Optional[str] = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None

class LoginHistory(BaseModel):
    user_id: Optional[str] = None
    username: str
    ip_address: str
    timestamp: datetime
    success: bool
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
