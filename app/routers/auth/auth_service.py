import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.routers.auth.auth_model import Token, TokenData, UserLogin, RefreshTokenRequest, RefreshToken, LoginHistory, LoginAttempt, LoginSettings
from app.routers.user.user_model import UserCreate
from app.routers.auth.auth_repository import AuthRepository
from app.routers.user.user_repository import UserRepository
from app.exceptions import UserException
from app.config import get_settings, Settings
from app.utils.performance import measure_time

class AuthService:
    def __init__(self) -> None:
        settings: Settings = get_settings()
        self.user_repository: UserRepository = UserRepository()
        self.auth_repository: AuthRepository = AuthRepository()
        self.pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY: str = settings.JWT_SECRET_KEY
        self.REFRESH_SECRET_KEY: str = settings.JWT_REFRESH_SECRET_KEY
        self.ALGORITHM: str = settings.JWT_ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        self.REFRESH_TOKEN_EXPIRE_MINUTES: int = int(settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
        
        # In-memory storage for refresh tokens
        # In production, this should be replaced with a database storage
        self.refresh_tokens: Dict[str, RefreshToken] = {}

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode: Dict[str, Any] = data.copy()
        if expires_delta:
            expire: datetime = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt: str = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
        
    def create_refresh_token(self, user_id: str, ip_address: str, user_agent: Optional[str] = None) -> str:
        # Generate a unique token
        token: str = str(uuid.uuid4())
        
        # Calculate expiration time
        expires_at: datetime = datetime.utcnow() + timedelta(minutes=self.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        # Create refresh token object
        refresh_token: RefreshToken = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store token in memory (in production, use a database)
        self.refresh_tokens[token] = refresh_token
        
        return token
        
    def verify_refresh_token(self, token: str) -> Optional[RefreshToken]:
        # Check if token exists in storage
        refresh_token: Optional[RefreshToken] = self.refresh_tokens.get(token)
        if not refresh_token:
            return None
            
        # Check if token is expired or revoked
        if refresh_token.revoked or (refresh_token.expires_at and refresh_token.expires_at < datetime.utcnow()):
            return None
            
        return refresh_token
        
    def revoke_refresh_token(self, token: str) -> bool:
        refresh_token: Optional[RefreshToken] = self.refresh_tokens.get(token)
        if not refresh_token:
            return False
            
        # Mark as revoked
        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.utcnow()
        self.refresh_tokens[token] = refresh_token
        
        return True
        
    async def refresh_access_token(self, refresh_token: str) -> Optional[Token]:
        token_data: Optional[RefreshToken] = self.verify_refresh_token(refresh_token)
        if not token_data:
            return None
            
        # Get user
        user: Optional[Dict[str, Any]] = await self.user_repository.find_by_id(token_data.user_id)
        if not user:
            return None
            
        # Create new access token
        access_token_expires: timedelta = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token: str = self.create_access_token(
            data={
                "sub": user["username"],
                "user_id": str(user["_id"]),
                "roles": user.get("roles", ["user"])
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep the same refresh token
            token_type="bearer",
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=self.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        )

    async def authenticate_user(self, username: str, password: str, ip_address: str) -> Optional[Dict[str, Any]]:
       """
       Authenticate user and track login attempts
       """
       # Record login attempt regardless of success
       await self.record_login_attempt(username, ip_address, False, "Starting authentication")
       
       # Get user
       user: Optional[Dict[str, Any]] = await self.user_repository.find_by_username(username, include_password=True)
       
       if not user:
           await self.record_login_attempt(username, ip_address, False, "User not found")
           return None
           
       # Check if user is locked using is_locked field
       if user.get("is_locked", False):
           await self.record_login_attempt(username, ip_address, False, "Account locked")
           raise UserException("Account is locked due to too many failed attempts", status_code=401)
           
       # Verify password
       password_verified: bool = self.verify_password(password, user["password"])
       
       if not password_verified:
           # Record failed attempt and increment failed login attempts
           await self.record_login_attempt(username, ip_address, False, "Invalid password")
           await self.increment_failed_attempts(str(user["_id"]))
           return None
           
       # Record successful login
       await self.record_login_attempt(username, ip_address, True)
       
       # Reset failed attempts on successful login
       await self.reset_failed_attempts(str(user["_id"]))
       
       # Update last login
       await self.update_user_last_login(str(user["_id"]), ip_address)
       
       return user

    async def increment_failed_attempts(self, user_id: str) -> None:
        """
        Increment failed login attempts and lock user if threshold reached
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            return
            
        current_attempts = user.get("failed_login_attempts", 0) + 1
        
        # Update failed attempts count
        update_data = {"failed_login_attempts": current_attempts}
        
        # Lock user if they reach 5 failed attempts
        if current_attempts >= 5:
            update_data["is_locked"] = True
            
        await self.user_repository.update_user(user_id, {"$set": update_data}, user_id)
        
    async def reset_failed_attempts(self, user_id: str) -> None:
        """
        Reset failed login attempts and unlock user
        """
        await self.user_repository.update_user(user_id, {
            "$set": {
                "failed_login_attempts": 0,
                "is_locked": False
            }
        }, user_id)

    async def record_login_attempt(self, username: str, ip_address: str, success: bool, reason: Optional[str] = None) -> None:
        """
        Record a login attempt in both login history and user's login history
        """
        user = await self.user_repository.find_by_username(username, include_password=True) if username else None
        
        # Prepare login history entry
        history = LoginHistory(
            username=username,
            user_id=str(user["_id"]) if user else None,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            success=success,
            reason=reason
        )
        
        # Store in login_history collection
        await self.auth_repository.add_login_history(history)

    async def update_user_last_login(self, user_id: str, ip_address: str) -> None:
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
        }, user_id)
        
        # Then update the login history array
        await self.user_repository.update_user(user_id, {
            "$push": {
                "login_history": {
                    "$each": [login_entry],
                    "$position": 0,  # Add to the beginning of the array
                    "$slice": 100  # Keep only the last 100 logins
                }
            }
        }, user_id)

    async def login(self, user_login: UserLogin, ip_address: str, user_agent: Optional[str] = None) -> Token:
        """
        Handle user login with rate limiting and tracking
        """
        user = await self.authenticate_user(user_login.username, user_login.password, ip_address)
        if not user:
            raise UserException("Invalid username or password", status_code=401)
        
        if not user.get("is_active", True):
            raise UserException("User account is disabled", status_code=401)

        # Create access token
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={
                "sub": user["username"],
                "user_id": str(user["_id"]),
                "roles": user.get("roles", ["user"])
            },
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = self.create_refresh_token(
            user_id=str(user["_id"]), 
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=self.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        )

    async def register(self, user: UserCreate) -> Dict[str, Any]:
        """
        Register a new user
        """
        # Hash password
        user.password = self.get_password_hash(user.password)
        
        # Create user
        from app.routers.user.user_service import UserService
        user_service = UserService()
        return await user_service.create_user(user, "")

    async def get_login_history(self, user_id: str) -> Optional[LoginAttempt]:
        """
        Get login history for a user
        """
        return await self.auth_repository.get_latest_attempts(user_id)

    async def verify_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username = payload.get("sub")
            user_id = payload.get("user_id")
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
        Unlock a user by resetting their failed attempts and is_locked flag
        
        Args:
            user_id: The ID of the user to unlock
            
        Returns:
            bool: True if the user was successfully unlocked, False otherwise
        """
        try:
            # Reset failed attempts and unlock user
            await self.reset_failed_attempts(user_id)
            # Also reset legacy login attempts for backward compatibility
            await self.auth_repository.delete_attempts(user_id)
            return True
        except Exception as e:
            print(f"Error unlocking user {user_id}: {str(e)}")
            return False
