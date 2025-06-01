import os
import asyncio
import sys
from typing import AsyncGenerator, Generator, Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from mongomock_motor import AsyncMongoMockClient
from bson import ObjectId
import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.config import get_settings
from app.database import get_database, get_client
# Mock user models for testing
class UserRole:
    USER = "user"
    ADMIN = "admin"

class UserCreate:
    def __init__(self, username, password, email, full_name):
        self.username = username
        self.password = password
        self.email = email
        self.full_name = full_name
from app.routers.auth.auth_service import AuthService
from app.routers.user.user_repository import UserRepository
from app.routers.auth.auth_repository import AuthRepository as LoginRepository

# Initialize settings
settings = get_settings()

# Apply patches for database connections
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    # Load test environment variables
    from dotenv import load_dotenv
    load_dotenv(".env.test")
    
    # Set default test values if not in .env.test
    test_config = {
        "MONGODB_URL": "mongomock://localhost",
        "MONGODB_DB": "test_db",
        "JWT_SECRET_KEY": "test-secret-key-1234567890",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "SECURITY_PASSWORD_SALT_ROUNDS": "10"
    }
    
    # Update with any values from .env.test
    test_config.update({k: v for k, v in os.environ.items() if k in test_config})
    
    with patch.dict(os.environ, test_config):
        yield

@pytest_asyncio.fixture
async def mock_mongodb_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create a mock MongoDB client using mongomock_motor."""
    # Create a mongomock_motor client
    mock_client = AsyncMongoMockClient()
    
    # Patch the get_client and get_database functions to use our mock client
    with patch('app.database.get_client', return_value=mock_client), \
         patch('app.database.get_database') as mock_get_db:
        
        # Configure the mock to return a database from our mock client
        mock_db = mock_client[settings.MONGODB_DB]
        mock_get_db.return_value = mock_db
        
        # Initialize collections with proper indexes
        await mock_db.users.create_index("username", unique=True)
        await mock_db.users.create_index("email", unique=True)
        await mock_db.login_attempts.create_index([("username", 1), ("ip_address", 1)])
        
        # Patch get_collection to return collections from our mock database
        original_get_collection = None
        try:
            from app.database import get_collection as original_get_collection
            
            async def mock_get_collection(collection_name: str):
                return mock_db[collection_name]
            
            with patch('app.database.get_collection', side_effect=mock_get_collection):
                yield mock_client
        finally:
            # Clean up
            if original_get_collection:
                patch('app.database.get_collection', original_get_collection).start()

@pytest_asyncio.fixture
async def mock_db(mock_mongodb_client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    """Get the mock database instance."""
    return mock_mongodb_client[settings.MONGODB_DB]

@pytest.fixture
def test_app():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest_asyncio.fixture
async def auth_service(mock_db):
    """Create an AuthService with mocked dependencies."""
    # The repositories will use the mocked database from the mock_db fixture
    # which is already set up to use mongomock
    from app.routers.user.user_repository import UserRepository
    from app.routers.auth.auth_repository import AuthRepository as LoginRepository
    from app.routers.auth.auth_service import AuthService
    
    # Create new instances for each test to avoid state leakage
    user_repo = UserRepository()
    login_repo = LoginRepository()
    
    # Initialize the auth service with the repositories
    auth_svc = AuthService(user_repo, login_repo)
    
    # Ensure the database is properly set up
    await mock_db.users.create_index("username", unique=True)
    await mock_db.users.create_index("email", unique=True)
    
    return auth_svc

@pytest_asyncio.fixture
async def user_repository(mock_db):
    """Get the UserRepository instance with a clean mock database."""
    from app.routers.user.user_repository import UserRepository
    # Clear any existing data
    await mock_db.users.delete_many({})
    return UserRepository()

@pytest_asyncio.fixture
async def login_repository(mock_db):
    """Get the LoginRepository instance with a clean mock database."""
    from app.routers.auth.auth_repository import AuthRepository as LoginRepository
    # Clear any existing data
    await mock_db.login_attempts.delete_many({})
    return LoginRepository()

@pytest_asyncio.fixture
async def test_user(auth_service):
    """Create a test user for authentication tests."""
    from app.models.user import UserCreate
    
    user = UserCreate(
        username="testuser",
        password="password123",
        email="test@example.com",
        full_name="Test User"
    )
    result = await auth_service.register(user)
    # Ensure the user was created successfully
    assert result is not None
    assert "_id" in result
    return result

@pytest_asyncio.fixture
async def test_admin(auth_service, user_repository):
    """Create a test admin user."""
    from app.models.user import UserCreate
    
    user = UserCreate(
        username="admin",
        password="admin123",
        email="admin@example.com",
        full_name="Admin User"
    )
    result = await auth_service.register(user)
    
    # Ensure the user was created successfully
    assert result is not None
    assert "_id" in result
    
    # Update user to admin role
    await user_repository.update_user(str(result["_id"]), {"$set": {"roles": ["admin"]}})
    
    # Refresh the user data
    updated_user = await user_repository.get_user_by_id(str(result["_id"]))
    assert updated_user is not None
    assert "admin" in updated_user.get("roles", [])
    
    return {"Authorization": f"Bearer {access_token}"}

# Define event loop for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
