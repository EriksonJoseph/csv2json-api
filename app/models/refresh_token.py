from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RefreshToken(BaseModel):
    user_id: str
    token: str
    expires_at: datetime
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class RefreshTokenInDB(RefreshToken):
    id: str
