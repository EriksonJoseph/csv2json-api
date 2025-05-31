from typing import Optional, Dict
from datetime import datetime
from app.database import get_collection
from app.routers.auth.auth_model import LoginHistory, LoginAttempt

class AuthRepository:
    async def add_login_history(self, history: LoginHistory):
        """
        Add a new login history record
        """
        login_history = await get_collection("login_history")
        await login_history.insert_one(history.dict())

    async def get_latest_attempts(self, user_id: str) -> Optional[LoginAttempt]:
        """
        Get the latest login attempts for a user
        """
        login_attempts = await get_collection("login_attempts")
        attempt = await login_attempts.find_one(
            {"user_id": user_id},
            sort=[("last_attempt", -1)]
        )
        if attempt:
            return LoginAttempt(**attempt)
        return None

    async def increment_attempts(self, user_id: str, ip_address: str):
        """
        Increment failed login attempts
        """
        login_attempts = await get_collection("login_attempts")
        now = datetime.utcnow()
        
        # Check if existing record exists
        existing = await login_attempts.find_one({"user_id": user_id})
        
        if existing:
            # Update existing record
            await login_attempts.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"attempts": 1},
                    "$set": {
                        "last_attempt": now,
                        "ip_address": ip_address
                    }
                }
            )
        else:
            # Create new record
            attempt = LoginAttempt(
                user_id=user_id,
                username="",  # Will be updated later
                attempts=1,
                last_attempt=now,
                ip_address=ip_address
            )
            await login_attempts.insert_one(attempt.dict())

    async def update_lock(self, user_id: str, locked_until: datetime):
        """
        Update account lock status
        """
        login_attempts = await get_collection("login_attempts")
        await login_attempts.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "locked_until": locked_until
                }
            }
        )

    async def reset_attempts(self, user_id: str):
        """
        Reset login attempts counter
        """
        login_attempts = await get_collection("login_attempts")
        await login_attempts.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "attempts": 0,
                    "locked_until": None,
                    "last_attempt": datetime.utcnow()
                }
            }
        )
        
    async def delete_attempts(self, user_id: str):
        """
        Delete all login attempts for a user
        """
        login_attempts = await get_collection("login_attempts")
        await login_attempts.delete_many({"user_id": user_id})
