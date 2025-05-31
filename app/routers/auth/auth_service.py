import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.routers.auth.auth_model import Token, TokenData, UserLogin, RefreshTokenRequest, RefreshToken, LoginHistory, LoginAttempt, LoginSettings
from app.routers.user.user_model import UserCreate
from app.routers.auth.auth_repository import AuthRepository
from app.routers.user.user_repository import UserRepository
from app.exceptions import UserException
from app.config import get_settings
from app.utils.performance import measure_time

class AuthService:
    def __init__(self):
        settings = get_settings()
        self.user_repository = UserRepository()
        self.auth_repository = AuthRepository()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = settings.JWT_SECRET_KEY
        self.REFRESH_SECRET_KEY = settings.JWT_REFRESH_SECRET_KEY
        self.ALGORITHM = settings.JWT_ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        self.REFRESH_TOKEN_EXPIRE_MINUTES = int(settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
        
        # In-memory storage for refresh tokens
        # In production, this should be replaced with a database storage
        self.refresh_tokens = {}

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
        
    def create_refresh_token(self, user_id: str, ip_address: str, user_agent: Optional[str] = None) -> str:
        # Generate a unique token
        token = str(uuid.uuid4())
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(minutes=self.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        # Create refresh token object
        refresh_token = RefreshToken(
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
        refresh_token = self.refresh_tokens.get(token)
        if not refresh_token:
            return None
            
        # Check if token is expired or revoked
        if refresh_token.revoked or refresh_token.expires_at < datetime.utcnow():
            return None
            
        return refresh_token
        
    def revoke_refresh_token(self, token: str) -> bool:
        refresh_token = self.refresh_tokens.get(token)
        if not refresh_token:
            return False
            
        # Mark as revoked
        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.utcnow()
        self.refresh_tokens[token] = refresh_token
        
        return True
        
    async def refresh_access_token(self, refresh_token: str) -> Optional[Token]:
        token_data = self.verify_refresh_token(refresh_token)
        if not token_data:
            return None
            
        # Get user
        user = await self.user_repository.find_by_id(token_data.user_id)
        if not user:
            return None
            
        # Create new access token
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
            refresh_token=refresh_token,  # Keep the same refresh token
            token_type="bearer",
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=self.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        )

    async def authenticate_user(self, username: str, password: str, ip_address: str) -> Optional[dict]:
       """
       Authenticate user and track login attempts
       """
       # Record login attempt regardless of success
       await self.record_login_attempt(username, ip_address, False, "Starting authentication")
       
       # Get user
       user = await self.user_repository.find_by_username(username, include_password=True)
       
       if not user:
           await self.record_login_attempt(username, ip_address, False, "User not found")
           return None
           
       # Check if user is locked
       user_id = str(user["_id"])
       is_locked = await self.is_user_locked(user_id)
       
       if is_locked:
           await self.record_login_attempt(username, ip_address, False, "Account locked")
           raise UserException("Account is locked due to too many failed attempts", status_code=401)
           
       # Verify password
       password_verified = self.verify_password(password, user["password"])
       
       if not password_verified:
           # Record failed attempt and increment counter
           await self.record_login_attempt(username, ip_address, False, "Invalid password")
           await self.auth_repository.increment_attempts(user_id, ip_address)
           return None
           
       # Record successful login
       await self.record_login_attempt(username, ip_address, True)
       
       # Reset failed attempts
       await self.auth_repository.reset_attempts(user_id)
       
       # Update last login
       await self.update_user_last_login(user_id, ip_address)
       
       return user

    async def is_user_locked(self, user_id: str) -> bool:
        """
        Check if user is locked due to too many failed attempts
        """
        # Get user login attempts
        attempts = await self.auth_repository.get_latest_attempts(user_id)
        if not attempts:
            return False
            
        # If no locked_until, not locked
        if not attempts.locked_until:
            # Check if we need to lock the account now
            if attempts.attempts >= 5:  # Hardcoded for now, move to settings later
                # Lock account for 30 minutes
                locked_until = datetime.utcnow() + timedelta(minutes=30)
                await self.auth_repository.update_lock(user_id, locked_until)
                return True
            return False
            
        # Check if lock has expired
        if attempts.locked_until < datetime.utcnow():
            # Lock has expired, reset
            await self.auth_repository.reset_attempts(user_id)
            return False
            
        # Account is locked
        return True

    async def record_login_attempt(self, username: str, ip_address: str, success: bool, reason: Optional[str] = None):
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

    async def register(self, user: UserCreate) -> Dict:
        """
        Register a new user
        """
        # Hash password
        user.password = self.get_password_hash(user.password)
        
        # Create user
        from app.routers.user.user_service import UserService
        user_service = UserService()
        return await user_service.create_user(user)

    async def get_login_history(self, user_id: str) -> LoginAttempt:
        """
        Get login history for a user
        """
        return await self.auth_repository.get_latest_attempts(user_id)

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
            await self.auth_repository.delete_attempts(user_id)
            return True
        except Exception as e:
            print(f"Error unlocking user {user_id}: {str(e)}")
            return False
