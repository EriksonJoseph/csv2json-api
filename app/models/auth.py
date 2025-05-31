from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

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
