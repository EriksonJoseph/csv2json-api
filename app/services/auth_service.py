import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.models.auth import Token, TokenData, UserLogin
from app.models.login import LoginHistory, LoginAttempt, LoginSettings
from app.models.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.exceptions import UserException
from app.repositories.login_repository import LoginRepository
from app.config import get_settings
from app.utils.performance import measure_time

class AuthService:
    def __init__(self, user_repository: UserRepository, login_repository: LoginRepository):
        settings = get_settings()
        self.user_repository = user_repository
        self.login_repository = login_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = settings.JWT_SECRET_KEY
        self.ALGORITHM = settings.JWT_ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        self.login_settings = LoginSettings()  # ตั้งค่า default login settings

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str, ip_address: str):
        """
        Authenticate user and track login attempts
        """
        # Get user with password
        user = await self.user_repository.get_user_by_username(username, include_password=True)
        if not user:
            await self.record_login_attempt(username, ip_address, False, "User not found")
            return False

        # Check if user is locked
        if await self.is_user_locked(user["_id"]):
            raise UserException("Account is locked. Please contact admin.", status_code=403)

        # Verify password
        if not self.verify_password(password, user["password"]):
            await self.record_login_attempt(username, ip_address, False, "Invalid password")
            return False

        # Record successful login
        await self.record_login_attempt(username, ip_address, True)
        await self.update_user_last_login(user["_id"], ip_address)
        
        # Remove password before returning
        if 'password' in user:
            del user['password']
            
        return user

    async def is_user_locked(self, user_id: str) -> bool:
        """
        Check if user is locked due to too many failed attempts
        """
        # Get latest login attempts
        attempts = await self.login_repository.get_latest_attempts(user_id)
        if not attempts:
            return False

        print(f"attemps {attempts}")
        # Check if locked
        now = datetime.utcnow()
        if attempts.locked_until and attempts.locked_until > now:
            return True

        # Check if we should reset attempts
        if (now - attempts.last_attempt).total_seconds() > (self.login_settings.reset_duration_minutes * 60):
            await self.login_repository.reset_attempts(user_id)
            return False

        # Check if too many attempts
        if attempts.attempts >= self.login_settings.max_attempts:
            # Lock account
            locked_until = now + timedelta(minutes=self.login_settings.lock_duration_minutes)
            await self.login_repository.update_lock(user_id, locked_until)
            return True

        return False

    async def record_login_attempt(self, username: str, ip_address: str, success: bool, reason: Optional[str] = None):
        """
        Record a login attempt in both login history and user's login history
        """
        user = await self.user_repository.get_user_by_username(username)
        if not user:
            return
            
        user_id = str(user["_id"])
        now = datetime.utcnow()
        status = "success" if success else "failure"
        
        # Prepare login history entry
        login_entry = {
            "login_at": now,
            "ip_address": ip_address,
            "status": status,
            "reason": reason
        }
        
        # Record in login history collection
        login_history = LoginHistory(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            login_at=now,
            status=status,
            reason=reason
        )
        await self.login_repository.add_login_history(login_history)
        
        # Update user's login history
        update_data = {
            "$push": {
                "login_history": {
                    "$each": [login_entry],
                    "$position": 0,  # Add to the beginning of the array
                    "$slice": 100  # Keep only the last 100 logins
                }
            }
        }
        await self.user_repository.update_user(user_id, update_data)
        
        # Update login attempts for failed logins
        if not success:
            await self.login_repository.increment_attempts(user_id, ip_address)

    async def update_user_last_login(self, user_id: str, ip_address: str):
        """
        Update user's last login timestamp, IP address, and add to login history
        """
        login_time = datetime.utcnow()
        login_entry = {
            "login_at": login_time,
            "ip_address": ip_address,
            "status": "success"
        }
        
        # First update the last login fields
        await self.user_repository.update_user(user_id, {
            "$set": {
                "last_login": login_time,
                "last_login_ip": ip_address
            }
        })
        
        # Then update the login history array
        await self.user_repository.update_user(user_id, {
            "$push": {
                "login_history": {
                    "$each": [login_entry],
                    "$position": 0,  # Add to the beginning of the array
                    "$slice": 100  # Keep only the last 100 logins
                }
            }
        })

    async def register(self, user: UserCreate) -> Dict:
        """
        Register a new user
        """
        # Hash password
        user.password = self.get_password_hash(user.password)
        
        # Create user
        from app.services.user_service import UserService
        user_service = UserService(self.user_repository)
        return await user_service.create_user(user)

    async def get_login_history(self, user_id: str) -> LoginAttempt:
        """
        Get login history for a user
        """
        return await self.login_repository.get_latest_attempts(user_id)
        
    async def unlock_user(self, user_id: str) -> bool:
        """
        Unlock a user by resetting their login attempts
        
        Args:
            user_id: The ID of the user to unlock
            
        Returns:
            bool: True if the user was successfully unlocked, False otherwise
        """
        try:
            # Reset login attempts
            await self.login_repository.delete_attempts(user_id)
            return True
        except Exception as e:
            print(f"Error unlocking user {user_id}: {str(e)}")
            return False

    async def record_login_attempt(self, username: str, ip_address: str, success: bool, reason: Optional[str] = None):
        """
        Record a login attempt in both login history and user's login history
        """
        user = await self.user_repository.get_user_by_username(username)
        if not user:
            return
            
        user_id = str(user["_id"])
        now = datetime.utcnow()
        status = "success" if success else "failure"
        
        # Prepare login history entry
        login_entry = {
            "login_at": now,
            "ip_address": ip_address,
            "status": status,
            "reason": reason
        }
        
        # Record in login history collection
        login_history = LoginHistory(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            login_at=now,
            status=status,
            reason=reason
        )
        await self.login_repository.add_login_history(login_history)
        
        # Update user's login history
        update_data = {
            "$push": {
                "login_history": {
                    "$each": [login_entry],
                    "$position": 0,  # Add to the beginning of the array
                    "$slice": 100  # Keep only the last 100 logins
                }
            }
        }
        await self.user_repository.update_user(user_id, update_data)
        
        # Update login attempts for failed logins
        if not success:
            await self.login_repository.increment_attempts(user_id, ip_address)

    async def update_user_last_login(self, user_id: str, ip_address: str):
        """
        Update user's last login timestamp, IP address, and add to login history
        """
        login_time = datetime.utcnow()
        login_entry = {
            "login_at": login_time,
            "ip_address": ip_address,
            "status": "success"
        }
        
        # First update the last login fields
        await self.user_repository.update_user(user_id, {
            "$set": {
                "last_login": login_time,
                "last_login_ip": ip_address
            }
        })
        
        # Then update the login history array
        await self.user_repository.update_user(user_id, {
            "$push": {
                "login_history": {
                    "$each": [login_entry],
                    "$position": 0,  # Add to the beginning of the array
                    "$slice": 100  # Keep only the last 100 logins
                }
            }
    })

    async def login(self, user_login: UserLogin, ip_address: str) -> Token:
        """
        Handle user login with rate limiting and tracking
        """
        user = await self.authenticate_user(user_login.username, user_login.password, ip_address)
        if not user:
            raise UserException("Invalid username or password", status_code=401)
        
        if not user.get("is_active", True):
            raise UserException("User account is disabled", status_code=401)

        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={
                "sub": user["username"],
                "user_id": str(user["_id"]),
                "roles": user.get("roles", ["user"])
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def register(self, user: UserCreate) -> Dict:
        """
        Register a new user
        """
        # Hash password
        user.password = self.get_password_hash(user.password)
        
        # Create user
        from app.services.user_service import UserService
        user_service = UserService(self.user_repository)
        return await user_service.create_user(user)

    async def get_login_history(self, user_id: str) -> LoginAttempt:
        """
        Get login history for a user
        """
        return await self.login_repository.get_latest_attempts(user_id)

    async def verify_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            roles: List[str] = payload.get("roles", [])
            
            if username is None or user_id is None:
                return None
                
            return TokenData(
                username=username,
                user_id=user_id,
                roles=roles
            )
        except JWTError:
            return None

    async def unlock_user(self, user_id: str) -> bool:
        """
        Unlock a user by resetting their login attempts
        
        Args:
            user_id: The ID of the user to unlock
            
        Returns:
            bool: True if the user was successfully unlocked, False otherwise
        """
        try:
            # Reset login attempts
            await self.login_repository.delete_attempts(user_id)
            return True
        except Exception as e:
            print(f"Error unlocking user {user_id}: {str(e)}")
            return False
